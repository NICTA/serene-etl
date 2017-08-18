import argparse
import collections
import os

DEFAULT_DIRECTORIES = ['/mnt/drive1', '/mnt/drive2', '/mnt/drive_etc']


def create_arguments():
    parser = argparse.ArgumentParser(prog='solr stats', add_help=True, description='Show Stats on SOLR nodes')

    parser.add_argument('start_dirs', help='directories', nargs='*', default=DEFAULT_DIRECTORIES)

    return parser


# Helper to run on each SOLR node if you want to have a look at the index sizes
def main():
    parser = create_arguments()
    args = parser.parse_args()

    # Update here for the scan directories
    start_dirs = args.start_dirs
    sizes = collections.defaultdict(int)

    for dir in start_dirs:
        for dirpath, dirname, filenames in os.walk(dir):
            for fn in filenames:
                sizes[fn.split('.')[-1]] += os.stat(os.path.join(dirpath, fn)).st_size

    ext_types = {
        'dvm': 'per document values (eg scoring factors)',
        'dvd': 'per document values (eg scoring factors)',

        'nvm': 'norms - length and boost factors',
        'nvd': 'norms - length and boost factors',

        'segments_i': 'info about a commit point',

        'tip': 'term dictionary index',
        'pos': 'term position in index',
        'tim': 'term index',
        'si': 'segment info - metadata',
        'fdt': 'stored fields',
        'doc': 'doc and frequencies of terms',
        'fdx': 'field index - pointers to stored data',
        'fnm': 'field names',
        'liv': 'info about which files are live'
    }
    groups = collections.defaultdict(int)
    total = 0

    for ext, size in sizes.iteritems():
        if ext in ext_types:
            file_type = ext_types[ext]
        else:
            file_type = 'other'
        groups[file_type] += size
        total += size

    for file_type, size in sorted(groups.iteritems(), key=lambda k: k[1], reverse=True):
        print('{:.0%}\t{}'.format(size/(total*1.0), file_type))

    print('Total: {:,} MB'.format(total / 1024/1024))


if __name__ == '__main__':
    main()
