import collections
import json
import logging
import subprocess
import os

from serene_load.helpers.containers.container_base import BaseContainer, FileContainer
from serene_metadata import REQUIRED_LOAD_FIELDS, PRIMARY_ID


class load_logger(object):
    @property
    def log(self):
        return logging.getLogger()


log = logging.getLogger()

#What characters are allowed in column names?
ALLOWED_COLUMN_NAME_CHARACTERS = 'abcdefghijklmnopqrstuvwxyz1234567890_'

COMPRESSION_RATIO = 15


def non_empty(f):
    if isinstance(f, basestring):
        return len(f.strip()) > 0
    else:
        return f is not None


class FileLoader(object):
    name = 'load_files'

    @staticmethod
    def func(args, task):
        bytes_processed = 0
        _output = task['output']
        with _output.open() as output:
            for infile in task['bucket']:
                try:
                    _accessor = BaseContainer.unpickle(infile.pop('accessor'), job_args=args)
                except KeyError:
                    _accessor = FileContainer(path=infile['path'], file=infile['file'], job_args=args)

                try:
                    # if encoding is passed from the command line, overwrite the detected encoding
                    enc = args.enc
                except AttributeError:
                    enc = infile['enc']

                log.debug('Using encoding {}'.format(enc))
                with _accessor as accessor:
                    iterator = task['processor'].process_file(args=args, meta=infile, fd=accessor.open())
                    bytes_processed = 0

                    primary_id = accessor.relative_path() + ':{}'
                    row = 0

                    for d in iterator:

                        d[PRIMARY_ID.name()] = primary_id.format(row)
                        row += 1
                        for r in REQUIRED_LOAD_FIELDS:
                            assert r in d, 'Processor has not added required field: {}\n{}'.format(r, json.dumps(d, indent=1))

                        # Check that column names are in ALLOWED_COLUMN_NAME_CHARACTERS
                        assert all(_ in ALLOWED_COLUMN_NAME_CHARACTERS for _ in ''.join(d.keys())), 'Not'

                        bytes_processed += output.write(
                            json.dumps(
                                # remove any empty fields
                                {k: v for k, v in filter(lambda _: non_empty(_[1]), d.iteritems())},
                                ensure_ascii=False).encode('utf-8') + '\n')

                        if bytes_processed > 100000000:
                            yield {
                                'proc_bytes': bytes_processed
                            }
                            bytes_processed = 0

                # cleanup
                yield {
                    'accessor': _accessor
                }

            # done processing infile
        # done processing bucket

        if bytes_processed:
            task['proc_bytes'] = bytes_processed

        del task['next_func']

        yield task


class OutputWriter(object):
    def __init__(self, cid, base_name):
        self.cid = cid
        self.base_name = base_name
        self.input_bytes = 0
        self.fd = None

    def __enter__(self):
        return self

    def write(self, data):
        self.fd.write(data)
        ld = len(data)
        self.input_bytes += ld
        return ld

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fd.flush()
        self.fd.close()
        return False

    def process_cmd(self):
        raise NotImplementedError()

    def cleanup_cmd(self):
        raise NotImplementedError()

    def cleanup(self):
        subprocess.check_call(' '.join(self.cleanup_cmd()), shell=True)

    def open(self):
        cmd = self.process_cmd()
        try:
            out = subprocess.Popen(' '.join(cmd), stdin=subprocess.PIPE, shell=True, universal_newlines=False)
        except OSError:
            raise
            # raise OSError('HDFS not on PATH')
        self.fd = out.stdin
        return self


class OutputToHDFS(OutputWriter):
    """
    Final file writer to HDFS
    """
    @property
    def output_file(self):
        return '/data/{:>08}/{}.json.bz2'.format(self.cid, self.base_name)

    def process_cmd(self):
        return ['bzip2', '-z', '-c', '-', '|', 'hdfs', 'dfs', '-put', '-', self.output_file]

    def cleanup_cmd(self):
        return ['hdfs', 'dfs', '-rm', self.output_file + '*']


class OutputToLocalFS(OutputWriter):
    """
    Output to local directory (for running locally)
    """
    @property
    def output_file(self):
        return 'output-data-{:>08}-{}.json.bz2'.format(self.cid, self.base_name)

    def process_cmd(self):
        return ['bzip2', '-z', '-c', '-', '>', self.output_file]

    def cleanup_cmd(self):
        return ['rm', self.output_file]


class JobProcessor(load_logger):
    """
    Base type for processing
    """
    # define filters that are applied to file metadata. Any files matching these filters will be processed by this processor
    FILTERS = [

    ]

    def __init__(self, arguments, worker):
        self.args = arguments if arguments else {}
        self.worker = worker

    def process(self, output, data):
        """
        Overwrite this function to process data

        Access input files via self.data
        """
        raise NotImplementedError()


class LoadedMeta(object):
    def __init__(self, loaded_path):
        self.loaded = loaded = collections.defaultdict(list)
        self.sizes = sizes = {}
        self.loaded_path = loaded_path

        for dirpath, dirnames, filenames in os.walk(loaded_path):
            for fn in filenames:
                if fn.endswith('.json'):

                    with open(os.path.join(dirpath, fn), 'r') as indata:

                        _fn = fn[:-5]

                        hashes = json.load(indata)
                        loaded[_fn].extend(hashes)

    def which_file(self, hash):
        """
        check if a file (hash) is already listed in a HDFS file
        returns the file name if it is, None if it is not listed
        """
        for filename, hashes in self.loaded.iteritems():
            if hash in hashes:
                return filename

        return None

    def output_bucket(self, filename, bucket):
        head, tail = os.path.split(filename)
        if tail:
            filename = tail
        output_file = os.path.join(self.loaded_path, filename + '.json')

        assert output_file.startswith(self.loaded_path)

        dst_head, dst_tail = os.path.split(output_file)

        try:
            os.makedirs(dst_head)
        except:
            pass

        with open(output_file, 'w') as outf:
            json.dump(
                [_['sha256'] for _ in bucket],
                outf,
                indent=1
            )

        log.debug('Wrote bucket to {}'.format(output_file))

    def layout_files(self, files, MIN_SIZE_MB=512):
        """
        create a proposed layout of files on HDFS
        if overwrite=True, replace existing files too

        new files not in loaded -> add
        existing files already in loaded -> dont_rewrite

        """
        already_placed = []
        not_yet_placed = []

        for _ in files:
            already = self.which_file(_['sha256'])

            if already:
                already_placed.append(_)
            else:
                not_yet_placed.append(_)

        log.info('BUCKET: {} files already loaded'.format(len(already_placed)))
        log.info('BUCKET: {} files not yet loaded'.format(len(not_yet_placed)))

        size_accessor = lambda _: _['bytes']
        bucket_size  = lambda b: sum(size_accessor(_) for _ in b)
        buckets = [
            []
        ]

        for f in sorted(not_yet_placed, key=size_accessor):

            smallest_bucket = sorted(buckets, key=bucket_size)[0]

            if bucket_size(smallest_bucket) > (COMPRESSION_RATIO * MIN_SIZE_MB * 1024 * 1024):
                bucket = []
                buckets.append(bucket)
            else:
                bucket = smallest_bucket

            bucket.append(f)

        return buckets
