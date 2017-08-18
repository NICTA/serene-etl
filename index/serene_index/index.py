import argparse
import importlib
import json
import logging
import os
import sys

from serene_metadata import CATALOGUE_ID
from helpers.catalogue_markings import get_markings
from helpers.update_helpers import LoadedMeta, generate_glob
from helpers.index_helpers import spark_wrapper, line_wrapper, mk_error_counter, print_stats

log = logging.getLogger()

try:
    # Setup PySpark if available
    import py4j
    import pyspark
    from pyspark.context import SparkContext
    from pyspark.sql import SQLContext, HiveContext
    from pyspark import SparkFiles

    sc = SparkContext()
    RUNSPARK = True
except ImportError:
    py4j = pyspark = SparkContext = SQLContext = HiveContext = SparkFiles = sc = sqlContext = None
    RUNSPARK = False

error_counter = mk_error_counter(sc)


class StoreNameValuePair(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        d = {}
        for value in values:
            try:
                n, v = value.split('=')
            except ValueError:
                raise ValueError('Not a valid key=value pair (unable to split): {}'.format(value))
            if n in d:
                if type(d[n]) is list:
                    d[n].append(v)
                else:
                    d[n] = [d[n], v]
            else:
                d[n] = v
        setattr(namespace, 'markings', d)


def create_arguments():
    """
        Parse arguments to INDEX
    """
    parser = argparse.ArgumentParser(prog='index', add_help=False, description='JSON >>> SOLR')

    common_args = [
        lambda _:_.add_argument('-b', metavar='base-path', dest='base', help='Base input path (defaults to /data)', default='/data'),
        lambda _:_.add_argument('-c', metavar='cid', dest='cid', type=int, help='Catalogue ID', required=True),
        lambda _:_.add_argument('--markings', type=unicode, help='Directory containing markings metadata (default is ./catalogue)', default='./catalogue'),
        lambda _:_.add_argument('--loaded', type=unicode, help='Directory containing loaded data (default is ./loaded)', default='./loaded'),
        lambda _:_.add_argument('--indexed', type=unicode, help='Directory containing indexed data (default is ./indexed)', default='./catalogue'),
        lambda _:_.add_argument('-m', metavar='module', dest='module', type=str, help='Module name used to process the dataset', required=True),
        lambda _:_.add_argument('--update', type=bool, default=True, help='True will not drop records for this CID before the start of this job (default). False will drop all previous documents (indexed before the start of this job)')
    ]

    subparsers = parser.add_subparsers(dest='mode')
    local_mode = subparsers.add_parser('local')
    spark_mode = subparsers.add_parser('spark')

    for _ in common_args:
        _(local_mode)
        _(spark_mode)

    local_mode.add_argument('--debug', action='store_true', help='Print output to STDOUT', default=False)
    local_mode.add_argument('--profile', action='store_true', help='Performance profile your module code', default=False)
    local_mode.add_argument('--stdin', action='store_true', help='Read data from STDIN')

    spark_mode.add_argument('--debug', action='store_true', help='Set spark log level to INFO (default is WARN)', default=False)
    spark_mode.add_argument('--hdfs', action='store_true', help='Write output to HDFS')
    spark_mode.add_argument('--avro', action='store_true', help="Write output to HDFS in avro format")
    spark_mode.add_argument('--avro_schema_package', action='store', help="Package which contains data/serene_model.avsc")
    spark_mode.add_argument('--partitions', type=int, help='How many partitions to use')
    spark_mode.add_argument('--solr', metavar='endpoint_url', help='Write output to SOLR')

    return parser


def proc_line(line, record_builder, metadata, args, error_counter):

    line_wrapper(line, record_builder, metadata, args, error_counter)
    error_counter.add('Processed line')


def setup_logging(LEVEL):

    logger = logging.getLogger()
    logger.setLevel(LEVEL)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(LEVEL)

    logger.addHandler(stream_handler)
    return logger


def run_job(args):
    log = setup_logging(LEVEL=logging.DEBUG if args.debug is True else logging.INFO)

    input_path = os.path.join(args.base, '{:0>8}'.format(args.cid))

    # get catalogue markings
    metadata = get_markings(args.markings, args.cid, {
        CATALOGUE_ID.name(): args.cid
    })

    log.info('Adding markings: \n{}'.format(json.dumps(metadata, indent=1, sort_keys=True)))

    log.debug('Determining files to index')

    loaded = LoadedMeta(args.loaded, cid=args.cid)
    indexed = LoadedMeta(args.indexed, cid=args.cid)

    file_list = []

    if args.update:
        # only process files that have >= 1 source file not in the index currently
        log.debug('Calculating files for updates only')

        for fn, hashes in loaded.loaded.iteritems():

            if filter(lambda _: indexed.which_file(_) is None, hashes):
                log.debug('Files needed in {}'.format(fn))
                file_list.append(fn)
            else:
                log.debug('No files needed in {}'.format(fn))

    else:
        log.debug('Processing all files')
        # process all files on disk
        file_list = loaded.loaded.keys()

    # now remove duplicate files
    deduped_files = []

    for fn in sorted(file_list):
        if all(loaded.which_file(_) > fn for _ in loaded.loaded[fn]):
            # for this filename and the hashes stored in it loaded.loaded[fn] are there "older" files which contain all it's hashes?
            log.debug('No files needed in {}'.format(fn))
        else:
            log.debug('At least one required file in {}'.format(fn))
            deduped_files.append(fn)

    log.info('Indexing {} files'.format(len(deduped_files)))

    fn_glob = '*'
    if len(deduped_files) != len(file_list):
        log.debug('{} files after de dupe ({} before)'.format(len(deduped_files), len(file_list)))

        yes_files = frozenset(deduped_files)
        all_files = frozenset(file_list)
        no_files = all_files - yes_files
        assert no_files
        fn_glob = generate_glob(deduped_files, no_files)

    input_files = [os.path.join(input_path, _) for _ in deduped_files]

    try:
        module = importlib.import_module('modules.module_' + args.module)
    except:
        module = importlib.import_module('serene_extra_modules.module_'+args.module)

    record_builder = getattr(module, 'record_builder', None)
    assert record_builder

    data_loader = getattr(module, 'dataset_loader', None)
    data_preprocess = getattr(module, 'data_preprocess', None)

    print 'Loaded module named {}: {}'.format(args.module, module)
    if args.mode == 'spark':
        assert RUNSPARK
        print 'Spark mode selected'

        if not args.solr:
            print 'WARNING - No solr endpoint specified - NOT INDEXING JUST PROCESSING'

        if args.debug is not True:
            # decrease verbosity of debuging
            logger = sc._jvm.org.apache.log4j
            logger.LogManager.getRootLogger().setLevel(logger.Level.WARN)

        spark_wrapper(input_files, metadata, record_builder, data_preprocess, args, sc, error_counter, data_loader)

    else:
        print 'Local mode selected'

        if args.stdin:
            print 'Reading data from STDIN'

            for line in sys.stdin:
                proc_line(line, record_builder, metadata, args, error_counter)
        else:
            print 'Scanning input path for JSON files'
            json_files = []
            for dirpath, dirnames, filenames in os.walk(input_path):
                for fn in filenames:
                    if fn.endswith('json'):
                        json_files.append(os.path.join(dirpath, fn))

            assert json_files, 'No .json files found under {}'.format(input_path)

            print '{} json files found to process'.format(len(json_files))
            for jf in json_files:
                with open(jf, 'r') as ijf:
                    for line in ijf:
                        proc_line(line, record_builder, metadata, args, error_counter)


def main():
    parser = create_arguments()
    args = parser.parse_args()

    if args.mode == 'local':
        if args.profile:
            print 'Profiling performance'
            import cProfile, pstats, StringIO
            pr = cProfile.Profile()
            pr.enable()

    try:
        run_job(args)
        print 'processing done'
    except:
        print 'Job interrupted'
        if sc is not None:
            sc.stop()

        print_stats(error_counter)
        raise

    if getattr(args, 'profile', False):
        pr.disable()
        s = StringIO.StringIO()
        sortby = 'tottime'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print '\n'.join(s.getvalue().split('\n')[:15])

    print_stats(error_counter)

if __name__ == '__main__':
    main()