#!/usr/bin/env python

# walk a path and generates a simple metadata catalogue of the files

import argparse
import json
import logging
import shutil
import subprocess
import tempfile
import os

from serene_load.helpers.containers.container_base import FileContainer, BaseContainer, TempFileContainer
from serene_load.meta_select import load_meta, VirtualMetaFile
from serene_load.helpers.multi_helper import MultiJob


def create_arguments():
    parser = argparse.ArgumentParser(description='scan')
    parser.add_argument('--base', type=unicode, help='Base path to scan', required=True)
    parser.add_argument('--subdir', type=unicode, help='Limit scan to a particular sub directory')
    parser.add_argument('--meta', type=unicode, help='Output path (default is ./metadata)', default='./metadata')
    parser.add_argument('--dont_unpack', help="Don't unpack files", action='store_true', default=False)
    parser.add_argument('--dont_hash', help="Don't hash files", action='store_true', default=False)
    parser.add_argument('--update', help="Only process new files", action='store_true', default=False)
    parser.add_argument('--verbose', help='Print verbose output', action='store_true')
    return parser


def check_dir(name, path):
    assert os.path.isdir(path), '{} "{}" is not a directory'.format(name, path)


def mk_file(fn, path, job_args):
    return {
        'next_func': 'scan',
        'file': fn,
        'path': path,
        'priority': 0,
        'accessor': FileContainer(path=path, file=fn, job_args=job_args)
    }


class ScanJob(MultiJob):
    def __init__(self, args):
        self.args = args

        self.logger = logger = logging.getLogger()

        logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG if args.verbose else logging.INFO)
        self.virtual_meta = {}
        self.existing_files_scanned = 0
        self.new_files_scanned = 0

        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        stream_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)

        self.tmp_output = tempfile.mktemp()
        os.makedirs(self.tmp_output)
        setattr(self.args, 'jobdir', self.tmp_output)

        self.rootdir = rootdir = os.path.normpath(args.base)
        check_dir('rootdir', rootdir)

        try:
            self.scandir = os.path.normpath(os.path.join(self.rootdir, args.subdir))
        except AttributeError:
            self.scandir = self.rootdir

        check_dir('scandir', self.scandir)

        self.output_dir = os.path.normpath(args.meta)
        self.mf = load_meta(self.output_dir)

        if not os.path.exists(self.output_dir):
            raise IOError('{} does not exist'.format(self.output_dir))

        self.logger.info('SCAN: {}'.format(self.scandir))

        self.files_found = 0
        self.files_output = 0

        self.setup_multi(self.args, load=0.95, available_functions='scan_helpers')

    def result(self, details):
        """
        See if we already have a hash for this file on disk
        """
        a = details.pop('accessor')
        assert isinstance(a, BaseContainer)

        if isinstance(a, TempFileContainer):
            path = details.pop('original_path')
            details['accessor'] = a.get_pickle()
        else:
            path = details['path']

        a.cleanup()  # remove temp files if this container created any...
        dir_meta_file = os.path.join(self.tmp_output, path, 'meta.json')
        dir_meta_path = os.path.join(self.tmp_output, path)

        if not os.path.exists(dir_meta_path):
            os.makedirs(dir_meta_path)

        try:
            filedata = self.virtual_meta[dir_meta_file]
        except KeyError:
            filedata = self.virtual_meta[dir_meta_file] = VirtualMetaFile(dir_meta_file)

        full_path = os.path.join(details['path'], details['file'])

        try:
            existing = details.pop('existing')
            self.existing_files_scanned += 1
        except KeyError:
            existing = False
            self.new_files_scanned += 1

        if 'didnt_unpack' in details:
            other_data = self.mf.subfile_match(details)
            self.logger.debug(u'found {} sub files for {}'.format(len(other_data), full_path))
            if other_data:
                filedata.add_objects(other_data)
            details.pop('didnt_unpack')

        if 'didnt_hash' in details:
            # Going to be missing sha256 and est_lines
            details.pop('didnt_hash')
            try:
                other_file = self.mf.exact_match(details)
                try:
                    details['sha256'] = other_file['sha256']
                    details['est_lines'] = other_file['est_lines']
                    if details != other_file:
                        self.logger.debug(u'previous details differ\nnew:\n{}\n\nold\n{}'.format(json.dumps(details, indent=1, sort_keys=True), json.dumps(other_file, indent=1, sort_keys=True)))
                        self.queue_work(mk_file(fn=details['file'], path=details['path'], job_args=self.args))
                except KeyError:
                    self.logger.debug(u'no previous hash found for {}'.format(full_path))

            except NameError:
                self.logger.debug(u'no previous file meta found for {}'.format(full_path))

        filedata.add_object(details)
        self.logger.debug(u'output: {}'.format(os.path.join(details['path'], details['file'])))

    def run(self):
        for dirpath, dirnames, filenames in os.walk(self.scandir):
            for filename in filenames:
                head = dirpath
                path = []
                while head != self.rootdir:
                    head, tail = os.path.split(head)
                    path.append(tail)

                path.reverse()
                rel_path = '/'.join(path)

                details = mk_file(fn=filename, path=rel_path, job_args=self.args)

                if self.args.update:
                    try:
                        self.mf.exact_match(details)
                        details.update({
                            'existing': True
                        })
                    except NameError:
                        # no existing file, proceed as normal
                        pass

                self.files_found += 1
                self.queue_work(details)

                if self.files_found % 1000:
                    self.manage_work()
                    self.print_progress()

        self.logger.info('DONE: {:,} files discovered'.format(self.files_found))

    def write_meta(self):
        self.logger.debug('Writing changed virtual meta files')
        for filename, vmf in self.virtual_meta.iteritems():
            if vmf.save():
                self.logger.debug('output {}'.format(filename))

    def sync(self):
        self.write_meta()

    def success(self):
        self.sync()

        try:
            subdir = os.path.normpath(self.args.subdir)
        except AttributeError:
            subdir = ''

        dst = os.path.join(self.output_dir, subdir)

        if os.path.exists(dst):
            self.logger.info('replacing {}'.format(dst))
            shutil.rmtree(dst)
        else:
            self.logger.info('copying to {}'.format(dst))

        dst_head, dst_tail = os.path.split(dst)

        try:
            os.makedirs(dst_head)
        except:
            pass
        src = os.path.join(self.tmp_output, subdir)

        shutil.move(src, dst_head)
        left_files = subprocess.check_output(['find', self.tmp_output, '-type', 'f'])
        assert not left_files, left_files
        shutil.rmtree(self.tmp_output)

        assert not self.args.cm.count()

        if self.args.update:
            self.logger.info('{} existing files scanned'.format(self.existing_files_scanned))
            self.logger.info('{} new files scanned'.format(self.new_files_scanned))
        else:
            self.logger.info('{} files scanned'.format(self.new_files_scanned))

    def failure(self):
        self.logger.debug('job cancelled - removing files :{}'.format(job.tmp_output))
        shutil.rmtree(job.tmp_output)


def main():
    parser = create_arguments()
    args = parser.parse_args()
    scan = ScanJob(args=args)
    scan.go()

if __name__ == '__main__':
    main()
