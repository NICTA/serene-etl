from pkg_resources import resource_string

import os
import random
import base64
import datetime
import json
import collections
from itertools import izip_longest
import traceback
import sys
import socket
from hashlib import sha256
import time
import math

import pysolr

from serene_schema import entities
from serene_schema.repr_to_solr import repr_to_solr, SOLREncoder
from serene_metadata import PRIMARY_ID, CATALOGUE_ID, validate_and_remove_metadata_during_record_index
from serene_metadata.config import SereneConfig

class IndexConfig(SereneConfig):
    SECTION_NAME = 'serene_index'

index_config = IndexConfig()


IDPARTS = frozenset([CATALOGUE_ID.name(), PRIMARY_ID.name()])

def mk_endpoint(_):
    return index_config.get('endpoint_url_fmt').format(random.randrange(8983, 8991))


def print_stats(ec):
    for k, v in sorted(ec.value.iteritems(), key=lambda sk: sk[0]):
        print u'{:,}\t{}'.format(v, k).encode('utf-8')


def mk_error_counter(sc=None):
    if sc:
        import pyspark

        class ErrorCounter(pyspark.accumulators.AccumulatorParam):
            def zero(self, value):
                return collections.defaultdict(int)

            def addInPlace(self, value1, value2):
                if isinstance(value2, basestring):
                    value1[value2] += 1
                else:
                    for k, v in value2.iteritems():
                        value1[k] += v
                return value1

        return sc.accumulator(collections.defaultdict(int), ErrorCounter())

    else:
        class ErrorCounter(object):
            def __init__(self):
                self.value = collections.defaultdict(int)

            def add(self, error):
                self.value[error] += 1

        return ErrorCounter()


def make_solr_document(r, builder, base, debug, error_counter):
    try:
        return _make_solr_document(r, builder, base, error_counter)
    except Exception as e:

        if debug:
            etype, value, tb = sys.exc_info()
            filename, lineno, name, line = traceback.extract_tb(tb)[-1]
            toprint = 'Exception in {}:{} in function {} - {}:{}'.format(filename, lineno, name, e.__class__.__name__, e.message)
            error_counter.add(toprint)
        else:
            print 'Exception on record:'
            print json.dumps(r, indent=1, sort_keys=True)
            raise


def _make_solr_document(r, builder, base, error_counter):
    """
        take an input row and build the Solr representation

        record - input record (a dictionary - a single record from the input data)
        builder - function that takes the input row as a dict and returns a serene_schema derived BaseSchema object
        base - default markings to apply to all documents

    """

    #add the base metadata to the record
    r.update(base)


    #the document ID is made up of IDPARTS (ie CATALOGUE_ID and PRIMARY_ID for the record)
    h = sha256()
    for _ in IDPARTS:
        if type(r[_]) is list:
            for __ in sorted(r[_]):
                h.update(str(__))
        else:
            h.update(str(r[_]))

    # Validate metadata against defined business rules from serene_metadata
    # and only valid metadata as defined in serene_metadata should be included on the record base by default
    out = validate_and_remove_metadata_during_record_index(r)
    metadata = out.copy()

    # add the document ID based on IDPARTS
    out['id'] = h.hexdigest()

    try:

        if '_load_error' in r:
            record = entities.Unknown(out['id'])
            try:
                r['_raw_line'] = base64.b64decode(r['_line_b64encoded']).decode('utf-8', 'replace')
            except:
                pass
        else:
            record = builder(r, error_counter, metadata)

        if record is None:
            record = entities.Unknown(out['id'])
        record.assert_real()
        repr_to_solr(repr=record.repr(), base=out)
        del record
    except Exception as e:
        print 'Exception on builder: {}'.format(e.message)
        print json.dumps(r, sort_keys=True, indent=1)
        raise

    # raw is included on the record base - but we have removed metadata fields already so they aren't double included
    out['raw'] = json.dumps(r, sort_keys=True, separators=(',', ':'), ensure_ascii=False, encoding='utf-8')

    return out

def grouper(n, iterable, fillvalue=None):
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


def index_docs(_docs):

    solr_endpoint = mk_endpoint(None)
    s = pysolr.Solr(solr_endpoint)

    total = 0

    for all_docs in grouper(int(index_config.get('max_index_size')), _docs):

        docs = filter(lambda _:_ is not None, all_docs)

        attempt_count = int(index_config.get('index_attempts'))

        while attempt_count > 0:
            try:
                # Force the documents to be committed, but don't wait until they are available
                s.add(docs, waitSearcher=False, commit=False, softCommit=False, waitFlush=False)
                total += len(docs)
                break
            except:
                attempt_count -= 1
                time.sleep(math.pow(2, int(index_config.get('index_attempts')) - attempt_count))

        if attempt_count <= 0:
            raise IndexError('Unable to index on {}'.format(solr_endpoint))

    return [total]


def default_loader(input_files, sc, args):
    executor_count = int(sc._conf.get('spark.executor.instances'))
    print input_files
    _set = sc.union([sc.textFile(_, use_unicode=False, minPartitions=executor_count*10).map(json.loads) for _ in input_files])
    return _set


def spark_wrapper(input_files, metadata, record_builder, data_preprocess, args, sc, error_counter, dataset_loader):
    if index_config.get('main_domain') in socket.getfqdn():
        sc.setCheckpointDir(index_config.get('checkpoint_dir_one').format(args.cid))
    else:
        sc.setCheckpointDir(index_config.get('checkpoint_dir_two').format(args.cid))

    if dataset_loader is None:
        dataset_loader = default_loader
    else:
        print 'Using custom dataset loader'

    input_set = dataset_loader(input_files, sc, args)

    # allow the module to do any pre-processing
    if data_preprocess:
        print '==> Preprocessing data using module'
        pre_processed = data_preprocess(input_set)
    else:
        pre_processed = input_set

    if pre_processed.__class__.__name__ == 'DataFrame':
        processed = pre_processed.rdd \
            .map(
                lambda r:
                    make_solr_document(
                        r=r.asDict(),
                        builder=record_builder,
                        base=metadata,
                        debug=args.debug,
                        error_counter=error_counter
                    )
            )
    else:
        processed = pre_processed \
            .map(
                lambda r:
                    make_solr_document(
                        r=r,
                        builder=record_builder,
                        base=metadata,
                        debug=args.debug,
                        error_counter=error_counter
                    )
            )

    if args.solr:
        print 'Indexing into SOLR'
        total = processed.mapPartitions(index_docs, preservesPartitioning=True).sum()
        print 'Done {} records'.format(total)
    else:
        print 'NOT indexing into SOLR'

    executor_count = int(sc._conf.get('spark.executor.instances'))

    if args.solr:
        import pysolr
        print 'Indexing complete.'
        print 'Commiting results'

        s = pysolr.Solr(args.solr)
        s.commit()

    now_str = datetime.datetime.now().isoformat()[:19].replace(':', '-')

    if args.hdfs:
        output_path = os.path.join('/output', '{:0>8}'.format(args.cid), now_str)
        print 'Saving JSON to {}'.format(output_path)
        processed \
            .map(lambda _: json.dumps(_)) \
            .saveAsTextFile(output_path, compressionCodecClass='org.apache.hadoop.io.compress.BZip2Codec')
        print 'Done'

    if args.avro and args.avro_schema_package:
        output_path = os.path.join('/output/avro/', '{:0>8}'.format(args.cid), now_str)
        avro_schema = resource_string(args.avro_schema_package, 'data/serene_model.avsc')
        print("Saving Avro to {0} with schema {1}".format(output_path, avro_schema))

        raise NotImplementedError()


def line_wrapper(line, record_builder, metadata, args, error_counter):
    doc = json.loads(line.strip())
    record = make_solr_document(doc, record_builder, metadata, args.debug, error_counter)
    if args.debug:
        print json.dumps(record, sort_keys=True, indent=1, cls=SOLREncoder)
