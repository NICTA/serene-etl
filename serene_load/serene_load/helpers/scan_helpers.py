from hashlib import sha256
from logging import getLogger
import chardet
import datetime
import os

from serene_load.helpers.containers.container_base import BUFSZ
from serene_load.helpers.containers.container_gzip import GzipFileProcessor
from serene_load.helpers.containers.container_libarchive import LibArchiveFileProcessor
from serene_load.helpers.containers.container_tar import TarFileProcessor
from serene_load.helpers.containers.container_zcat import ZCatFileProcessor
from serene_load.helpers.containers.container_zip import ZipFileProcessor
from serene_load.helpers.containers.container_7za import SevenZipFileProcessor
from serene_load.helpers.file_helpers import si_size, mime_type, enc_type

log = getLogger()

processors = [
    ZipFileProcessor,
    TarFileProcessor,
    GzipFileProcessor,
    LibArchiveFileProcessor,
    ZCatFileProcessor,
    SevenZipFileProcessor
]


def detect_container(args, f):
    """
    Given input_file - a file like object that supports open(), determine what kind of container we have...
    """
    for proc in processors:
        try:
            if proc.mime_test(f) is False:
                continue
        except NotImplementedError:
            pass

        if proc.valid(args, f['accessor']):
            log.debug(u'{} matched {}'.format(proc.__name__, f['accessor']))
            return proc

    log.debug(u'{} not a container'.format(f['accessor']))
    return None


class ScanFile(object):
    name = 'scan'

    @staticmethod
    def func(args, input):
        """
        scan a file on the filesystem
        """

        with input['accessor'] as accessor:

            path = accessor.instantiate_file()

            stats = os.stat(path)

            input.update({
                'next_func': 'hash',
                'bytes': stats.st_size,
                'proc_bytes': 10,
                'size': '{0:.1S}'.format(si_size(stats.st_size)),
                'ctime': datetime.datetime.fromtimestamp(stats.st_ctime).isoformat()[:19],
                'mtime': datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()[:19]
            })

        yield input


# 4MB

class HashFile(object):
    name = 'hash'

    @staticmethod
    def func(args, f):
        sha = sha256()
        i = 0

        with f['accessor'] as accessor:
            fd = accessor.open()

            chunk = fd.read(BUFSZ)
            sha.update(chunk)
            i += len(chunk)
            f.update({
                'mime': mime_type.from_buffer(chunk),
                'enc': enc_type.from_buffer(chunk),
            })
            lines_in_chunk = len(chunk.split('\n'))
            yield {'proc_bytes': BUFSZ * 3}

            if f['enc'] != 'binary':
                # chardet is expensive - only use it on non-binary files...
                f.update({'enc': chardet.detect(chunk)['encoding']})
                yield {'proc_bytes': BUFSZ}

            if args.dont_hash or (args.update and 'existing' in f):
                f.update({
                    'didnt_hash': True
                })

            else:
                log.debug(u'start hash of {}'.format(f['accessor']))
                try:
                    while True:
                        chunk = fd.read(BUFSZ)
                        if not chunk:
                            break
                        i += len(chunk)
                        sha.update(chunk)
                        yield {
                            'proc_bytes': BUFSZ
                        }

                except EOFError:
                    pass

                log.debug(u'done hash of {}'.format(f['accessor']))
                if 'bytes' in f:
                    assert f['bytes'] == i, 'Length mismatch when computing SHA: {}'.format(f)

                f.update({
                    'sha256': sha.hexdigest(),
                    'est_lines': int(float(lines_in_chunk * i) / BUFSZ),
                    'size': '{0:.1S}'.format(si_size(i)),
                    'bytes': i
                })

        if f['enc'] and f['enc'].startswith('text'):
            # don't try to unpack text!
            del f['next_func']
        else:
            f['next_func'] = 'unpack'

        yield f


DOCX_DONT_UNPACK = [
    ("excel", ".xlsx"),
    ("word", ".docx"),
    ("powerpoint", ".pptx")
]


class UnpackMulti(object):
    name = 'unpack'

    @staticmethod
    def func(args, f):
        original_path = f['path'] if 'original_path' not in f else f['original_path']
        unpack = True

        for mdu, edu in DOCX_DONT_UNPACK:
            if mdu in f['mime'] or f['file'].lower().endswith(edu):
                unpack = False

        if unpack and f['bytes'] > 0:
            if args.dont_unpack is True or (args.update and 'existing' in f):
                f['didnt_unpack'] = True
            else:
                ctype = detect_container(args, f)

                if ctype:
                    f['proc_bytes'] = 0
                    for b in ctype.unpack(args, f['accessor']):

                        if len(b.keys()) > 1 and 'original_path' not in b:
                            b['original_path'] = original_path

                        yield b

        del f['next_func']
        yield f
