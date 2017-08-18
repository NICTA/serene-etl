import collections
import json
import re
import logging
import os
log = logging.getLogger()


class LoadedMeta(object):

    def __init__(self, loaded_path, cid):

        self.loaded = loaded = collections.defaultdict(list)
        loaded_path = os.path.join(loaded_path, '{:0>8}'.format(cid))

        log.info('Loading from {}'.format(loaded_path))

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
        the ordering is important so we return the "largest / newest" file that contains the hash
        """

        for filename, hashes in sorted(self.loaded.iteritems(), key=lambda k: k[0], reverse=True):
            if hash in hashes:
                return filename

        return None


def generate_glob(yes_list, no_list):
    """generate a glob that matches all of yes_list and none of no_list
    """

    yl = set(yes_list)
    nl = set(no_list)

    assert yl.difference(nl), 'They are the same list'

    common_prefix = os.path.commonprefix(yes_list)

    sey_list = [list(''+_) for _ in yes_list]
    [_.reverse() for _ in sey_list]
    sey_list = [''.join(_) for _ in sey_list]

    common_suffix = list(os.path.commonprefix(sey_list))
    common_suffix.reverse()
    common_suffix = ''.join(common_suffix)

    print common_prefix
    print common_suffix

    if common_prefix and common_suffix:
        match = re.compile('{}.*{}'.format(common_prefix, common_suffix))
        if all(match.match(_) is None for _ in no_list):
            # pattern doesn't match any in the no_list
            if common_suffix == common_prefix:
                return common_prefix + '*'
            return '{}*{}'.format(common_prefix, common_suffix)

    return None
