from pip._vendor.distlib._backport import tarfile as _tarfile
import logging

import datetime
from serene_load.helpers.containers.container_base import TempFileContainer, BaseContainer, BaseProcessor
from ..file_helpers import si_size
log = logging.getLogger()


class TarFileContainer(TempFileContainer):
    def decompress(self, source, target):
        tar = _tarfile.open(name=source, mode='r')
        tar.members.append(self.args['member'])
        fd = tar.extractfile(self.args['member'])
        self.write_fd(fd, target)

    def filename(self):
        return self.args['member'].name

BaseContainer.add_container_type(TarFileContainer)


class TarFileProcessor(BaseProcessor):
    @classmethod
    def mime_test(cls, f):
        if 'tar' not in f['mime']:
            return False

    @classmethod
    def valid(cls, args, input_file):
        with input_file as infile:
            fp = infile.instantiate_file()
            try:
                tar = _tarfile.TarFile.open(name=fp, mode='r')
                tar.close()
                return True
            except:
                return False

    @classmethod
    def unpack(cls, args, input_file):
        with input_file as infile:
            fd = infile.open()
            tar = _tarfile.open(name=None, mode='r', fileobj=fd)

            log.debug(u'{} started get members'.format(input_file))
            tar.getmembers()
            log.debug(u'{} done get members'.format(input_file))

            yield {
                'proc_bytes': sum(_.size for _ in tar.members)
            }

            for _ in tar.members:
                if _.size == 0:
                    continue

                container = TarFileContainer(input_fd=input_file, member=_, job_args=args)
                mtime = datetime.datetime.fromtimestamp(_.mtime)

                yield {
                    'next_func': 'hash',
                    'accessor': container,
                    'file': _.name,
                    'mtime': mtime.isoformat()[:19],
                    'path': container.parent_path(),
                    'bytes': _.size,
                    'size': '{0:.1S}'.format(si_size(_.size))
                }
