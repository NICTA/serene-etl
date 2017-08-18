import zipfile
import datetime
from serene_load.helpers.containers.container_base import BaseContainer, TempFileContainer, BaseProcessor
from ..file_helpers import si_size
import logging
log = logging.getLogger()


class ZipFileContainer(TempFileContainer):
    def decompress(self, source, target):
        zip = zipfile.ZipFile(file=source)
        fd = zip.open(self.args['zipinfo'])
        self.write_fd(fd, target)

    def filename(self):
        return self.args['zipinfo'].filename

BaseContainer.add_container_type(ZipFileContainer)


class ZipFileProcessor(BaseProcessor):
    @classmethod
    def valid(cls, args, input_file):
        with input_file as infile:
            fp = infile.instantiate_file()
            try:
                zipfile.ZipFile(file=fp)
                return True
            except:
                return False

    @classmethod
    def unpack(cls, args, input_file):
        with input_file as infile:
            fp = infile.instantiate_file()
            zip = zipfile.ZipFile(file=fp)

            for _ in zip.filelist:
                if _.file_size == 0:
                    continue

                accessor = ZipFileContainer(input_fd=input_file, zipinfo=_, job_args=args)

                yield {
                    'next_func': 'hash',
                    'file': _.filename,
                    'path': accessor.parent().relative_path(),
                    'bytes': _.file_size,
                    'size': '{0:.1S}'.format(si_size(_.file_size)),
                    'mtime': datetime.datetime(year=_.date_time[0], month=_.date_time[1], day=_.date_time[2],
                                               hour=_.date_time[3], minute=_.date_time[4],
                                               second=_.date_time[5]).isoformat()[:19],
                    'accessor': accessor
                }
