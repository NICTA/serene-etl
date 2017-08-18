from serene_load.helpers.containers.container_base import TempFileContainer, BaseProcessor, BaseContainer
from libarchive import is_archive, SeekableArchive
import logging
import datetime

log = logging.getLogger()
# monkeypatch_io(EntryReadStream)


class LibArchiveFileContainer(TempFileContainer):
    def decompress(self, source, target):
        archive = SeekableArchive(source)
        fd = archive.readstream(self.args['pathname'])
        self.write_fd(fd, target)

    def filename(self):
        return self.args['pathname']

BaseContainer.add_container_type(LibArchiveFileContainer)


class LibArchiveFileProcessor(BaseProcessor):
    @classmethod
    def valid(cls, args, input_file):
        with input_file as infile:
            filename = input_file.instantiate_file()

            if is_archive(filename) is False:
                return False

            archive = SeekableArchive(filename)
            if archive.format is None:
                return False

            try:
                for _ in archive:
                    pass
            except:
                return False

            log.debug(u'LIBARCHIVE: detected {} file'.format(archive.format))
            return True

    @classmethod
    def unpack(cls, args, input_file):

        with input_file as infile:

            filename = infile.instantiate_file()
            archive = SeekableArchive(filename)

            for entry in archive:
                log.debug(u'{} found in {}'.format(entry.pathname, input_file.relative_path()))
                accessor = LibArchiveFileContainer(input_fd=input_file, pathname=entry.pathname, job_args=args)
                yield {
                    'next_func': 'hash',
                    'accessor': accessor,
                    'file': entry.pathname,
                    'mtime': datetime.datetime.fromtimestamp(entry.mtime).isoformat()[:19],
                    'path': accessor.parent().relative_path()
                }
