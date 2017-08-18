#!/usr/bin/env python

# Script that scans /data (or a subdirectory) and generates the simplest representation of the metadata and stats about files

import argparse
import json
import collections
import os
import re
import logging

log = logging.getLogger()


def mk_filter(f):
    if f.startswith('!'):
        check = lambda _: _ == 0
        f = f[1:]
    else:
        check = lambda _: _ > 0

    def func(meta):
        matches = 0
        for k, v in meta.iteritems():
            line = '{}={}'.format(k, v)
            if re.search(f, line, re.IGNORECASE):
                matches += 1
        return check(matches)
    return func


class VirtualMetaFile(object):
    """
    append only....
    """
    def __init__(self, fs_path):
        self.fs_path = fs_path
        self.data = []
        self.insync = True

    def save(self):
        if self.insync:
            return False

        filedata = sorted(self.data, key=lambda k: os.path.join(k['path'], k['file']))
        with open(self.fs_path, 'w') as fobj:
            json.dump(filedata, fobj, indent=1, sort_keys=True)

        self.insync = True
        return True

    def add_object(self, obj):
        self.data.append(obj)
        self.insync = False

    def add_objects(self, objects):
        self.data.extend(objects)
        self.insync = False


class MetaFiltered(object):
    def __init__(self):
        self.all_files = []
        self.path_map = {}
        self.subpath_map = {}

    def load_meta(self, source):
        with open(source, 'r') as mdf:
            return json.load(mdf)

    def add_source(self, source):
        meta = self.load_meta(source)
        self.all_files.extend(meta)
        for m in meta:
            fp = os.path.join(m['path'], m['file'])
            assert fp not in m
            self.path_map[fp] = m

    def __len__(self):
        return len(self.all_files)

    def filter_meta(self, filters):
        begin = self.all_files[:]
        for f in filters:
            begin = filter(mk_filter(f), begin)
        return begin

    def all(self):
        return self.all_files

    def subfile_match(self, details, include_children=True):
        """
        Find all files that are underneath this file
        """
        full_path = os.path.join(details['path'], details['file'])
        # filter = 'path={}$'.format(full_path)
        # filter2 = 'path={}/.+$'.format(full_path)

        try:
            m1 = [self.path_map[full_path]]
        except KeyError:
            m1 = []

        if include_children:
            try:
                m2 = self.subpath_map[full_path]
            except KeyError:
                m2 = [
                    self.path_map[_] for _ in filter(lambda _:_.startswith(full_path + '/'), self.path_map.keys())
                ]
                self.subpath_map[full_path] = m2
        else:
            m2 = []

        return m1 + m2

    def exact_match(self, details):
        matches = self.subfile_match(details, include_children=False)
        # filter = 'path={}$'.format(re.escape(details['path']))
        # filter2 = 'file={}$'.format(re.escape(details['file']))
        if len(matches) == 0:
            raise NameError
        if len(matches) > 1:
            raise Exception('multiple matches for {}/{}'.format(details['path'], details['file']))
        return matches[0]

    def dedupe(self, filtered):
        seen = set()
        deduped = []
        for _ in sorted(filtered, key=lambda _: os.path.join(_['path'], _['file'])):
            if _['sha256'] in seen:
                continue
            seen.add(_['sha256'])
            deduped.append(_)

        removed = len(filtered) - len(deduped)
        if removed:
            log.info('DEDUPE: {:,} duplicates removed'.format(removed))
        return deduped


def create_arguments():
    parser = argparse.ArgumentParser(description='metadata select')
    parser.add_argument('--meta', type=unicode, help='Location of metadata files (defaults to ./metadata)', default='./metadata')
    parser.add_argument('--subdir', type=unicode, help='Subdirectory of interest')
    parser.add_argument('--ignore', action='store_true', help='Ignore errors in .meta files')
    parser.add_argument('--allow-duplicates', help='Dont remove sha256 dupes', action='store_true', default=False)
    parser.add_argument('--print-duplicates', help='output filenames of duplicates', action='store_true', default=False)
    parser.add_argument('--output', metavar="FILE", help='output json to FILE or stdout if -')
    parser.add_argument('--sum', metavar="SUM", help='sum argument and print total')
    parser.add_argument('filter', nargs='*', help='Filter results based on regex to apply (all filters must match)')
    return parser


def load_meta(scandir, ignore_errors=False):
    mf = MetaFiltered()
    for path, dir, files in os.walk(scandir):
        for fn in files:
            if fn == 'meta.json':
                try:
                    mf.add_source(os.path.join(path, fn))
                except:
                    if ignore_errors:
                        continue
                    else:
                        raise IOError('Meta file appears corrupt: {}'.format(os.path.join(path, fn)))

    return mf


def main():
    parser = create_arguments()
    args = parser.parse_args()

    try:
        scandir = os.path.normpath(os.path.join(args.meta, args.subdir))
    except AttributeError:
        scandir = os.path.normpath(os.path.join(args.meta))

    assert os.path.exists(scandir), '{} does not exist'.format(scandir)

    mf = load_meta(scandir, args.ignore)
    print '{:,} metadata items found under {}'.format(len(mf), scandir)
    filtered = mf.filter_meta(args.filter)

    if args.print_duplicates is True:
        seen = collections.defaultdict(list)
        for _ in sorted(filtered, key=lambda _: os.path.join(_['path'], _['file'])):
            seen[_['sha256']].append(os.path.join(_['path'], _['file']))

        for sha, files in seen.iteritems():
            if len(files) == 1:
                continue

            max_path = max(len(_) for _ in files)
            fmt = '{:>' + str(max_path) + '}'

            print '{} duplicates ({})'.format(len(files), sha)

            for f in files:
                print fmt.format(f)
            print ''

    elif args.allow_duplicates is False:
        filtered = mf.dedupe(filtered)

    total = sum(int(_['bytes']) for _ in filtered)
    print '{:,} files matched your filters ({:,} bytes)'.format(len(filtered), total)

    if args.output:
        if args.output == '-':
            print json.dumps(filtered, indent=1, sort_keys=True)
        else:
            with open(args.output, 'w') as outfile:
                json.dump(filtered, outfile, indent=1, sort_keys=True)
            print 'wrote output to {}'.format(args.output)

if __name__ == '__main__':
    main()
