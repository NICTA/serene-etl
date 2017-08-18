import argparse
import datetime
import importlib
import inspect
import json
import logging
import shutil
import tempfile

import os
from serene_load.meta_select import load_meta
from serene_load.helpers.multi_helper import MultiJob
from serene_load.helpers.file_helpers import si_size
from serene_load.helpers.load_helpers import JobProcessor, LoadedMeta, OutputToHDFS, OutputToLocalFS

from serene_load.helpers.containers import container_base # pylint: disable=unused-import # Required for registry creation
from serene_load.helpers.containers import container_7za, container_gzip, container_libarchive, container_tar, container_zcat, container_zip # pylint: disable=unused-import # Required for registry creation


def create_arguments():
    parser = argparse.ArgumentParser(description='load data to hdfs')
    parser.add_argument('--base', type=unicode, help='Base directory', required=True)
    parser.add_argument('--cid', type=int, help='Catalogue ID', required=True)
    parser.add_argument('--meta', type=unicode, help='Directory containing file metadata (default is ./metadata)', default='./metadata')
    parser.add_argument('--loaded', type=unicode, help='Directory containing load metadata (default is ./loaded)', default='./loaded')
    parser.add_argument('filter', nargs='*', help='Filter results based on regex to apply (all filters must match)')
    parser.add_argument('--processor', type=unicode, help='Processor module to run', required=True)
    parser.add_argument('--other_package', type=unicode, help='name of extra packages with processors', required=False, default='serene_extra_processors')
    parser.add_argument('--arguments', type=json.loads, help='Arguments to pass to processor', required=False)
    parser.add_argument('--local', action='store_true', help='Run locally', default=False)
    parser.add_argument('--debug', action='store_true', help='More verbose debug output')
    return parser


def setup_logging(LEVEL):
    logger = logging.getLogger()
    logger.setLevel(LEVEL)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(LEVEL)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    return logger


class LoadJob(MultiJob):
    def __init__(self, args):
        self.args = args
        self.log = log = setup_logging(LEVEL=logging.DEBUG if args.debug is True else logging.INFO)

        cid = '{:>08}'.format(args.cid)
        data_source_path = os.path.join(args.base, cid)

        self.tmp_output = tempfile.mktemp()
        os.makedirs(self.tmp_output)
        setattr(self.args, 'jobdir', self.tmp_output)

        # load processor module - check ./ then another package when we've decided what it'll be
        try:
            proc = importlib.import_module('serene_load.processors.proc_' + args.processor)
        except ImportError:
            log.info("Did not find {0} in internal processors, checking package {1}".format(args.processor, args.other_package))
            try:
                proc = importlib.import_module('{}.proc_{}'.format(args.other_package, args.processor))
            except ImportError:
                log.fatal("Could not import processor {0}".format(args.processor))
                assert False, "Could not import processor {0}".format(args.processor)

        self.processors = processors = inspect.getmembers(proc, lambda _: inspect.isclass(_) and _ != JobProcessor and issubclass(_, JobProcessor))
        assert processors, 'No subclasses of JobProcessor found in proc_{}.py'.format(args.processor)

        for name, proc in processors:
            log.info('LOADED PROC: {} {}'.format(name, proc))

        meta_path = os.path.normpath(os.path.join(args.meta, cid))
        mf = load_meta(meta_path)

        filters = [
            'path={:>08}.*'.format(args.cid)
        ]

        log.debug('METADATA: {} files loaded from {}'.format(len(mf), meta_path))

        if args.arguments:
            for k, v in args.arguments.iteritems():
                assert getattr(self.args, k, None) is None
                setattr(self.args, k, v)
                self.log.info('User specified {} = {}'.format(k, v))

        self.proc_files = proc_files = {}
        all_files = mf.filter_meta(filters)
        matched_files = []

        for name, proc in processors:
            this_proc = mf.filter_meta(filters + args.filter + proc.FILTERS)

            for f in this_proc:
                # fixme ? check if name here is actually clobbering the outer name in the logging below..?
                for _, files in proc_files.iteritems():
                    assert f not in files, '{} is marked to be processed by multiple processors'.format(os.path.join(f['path'], f['name']))

            log.info('PROC: {} has {} files after filtering'.format(name, len(this_proc)))
            proc_files[name] = mf.dedupe(this_proc)
            log.info('PROC: {} has {} files after removing duplicates'.format(name, len(proc_files[name])))
            matched_files.extend(proc_files[name])

            for k, v in getattr(proc, 'ARGS', {}).iteritems():
                if getattr(self.args, k, None) is None:
                    setattr(self.args, k, v)
                    self.log.info('Proc: {} overwrote {} = {}'.format(proc, k, v))

        total_bytes = sum(_['bytes'] for _ in all_files)
        matched_bytes = sum(_['bytes'] for _ in matched_files)

        log.warn('FOUND: {:.0S} in {} files listed in meta for {}'.format(si_size(total_bytes), len(all_files), cid))
        log.warn('FOUND: {:.0S} in {} files to be processed'.format(si_size(matched_bytes), len(matched_files)))
        if total_bytes - matched_bytes:
            log.warn('FOUND: (NB NOT PROCESSING {:.0S})'.format(si_size(total_bytes - matched_bytes)))

        loaded_path = os.path.normpath(os.path.join(args.loaded, cid))

        self.loaded_meta = LoadedMeta(loaded_path)
        self.datestamp = datetime.datetime.now().isoformat()[:19].replace(':', '')
        self.setup_multi(args, available_functions='load_helpers', load=1)

    def run(self):
        for name, proc in self.processors:
            load_size = 0
            buckets = self.loaded_meta.layout_files(self.proc_files[name], MIN_SIZE_MB=16 if self.args.debug else 512)
            for i, bucket in enumerate(buckets):

                if not bucket:
                    continue

                base_name = '{}_{}_{}'.format(name, self.datestamp, i)
                writer = OutputToLocalFS if self.args.local else OutputToHDFS
                job = {
                    'next_func': 'load_files',
                    'base_name': base_name,
                    'priority': 0,
                    'processor': proc,
                    'output': writer(self.args.cid, base_name),
                    'cleanup': 'output',
                    'bucket': bucket
                }
                self.queue_work(job)
                load_size += sum(_['bytes'] for _ in bucket)

            if load_size:
                self.log.info('QUEUED : {} - {:.0S} input data to process'.format(name, si_size(load_size)))
            else:
                self.log.info('Nothing to process: {}'.format(name))

    def result(self, result):
        # result is a dictionary of file names as keys and value as
        try:
            a = result.pop('accessor')
            a.cleanup()  # remove temp files if this container created any...
            return
        except KeyError:
            pass

        filename = result['output'].output_file
        self.loaded_meta.output_bucket(filename=filename, bucket=result['bucket'])
        self.log.warn('DONE: {}'.format(filename))

    def success(self):
        self.cleanup()
        self.log.warn('SUCCESS')

    def failure(self):
        self.cleanup()
        self.log.warn('FAILURE')

    def cleanup(self):
        self.print_error_log()
        self.log.debug('Cleanup removing {}'.format(self.tmp_output))
        shutil.rmtree(self.tmp_output)


def main():
    parser = create_arguments()
    args = parser.parse_args()
    load = LoadJob(args=args)
    load.go()

if __name__ == '__main__':
    main()
