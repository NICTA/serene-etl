import gzip
import logging
import subprocess
import os
import io
from serene_load.helpers.containers.container_base import TempFileContainer, BaseContainer, BaseProcessor

log = logging.getLogger()


class GzipFileContainer(TempFileContainer):
    def decompress(self, source, target):
        subprocess.check_call('/usr/bin/gzip -cd "{}" > {}'.format(source, target), stderr=io.open('/dev/null', 'w'), shell=True)

    def filename(self):
        pp = self.parent_path()
        fullpath, ext = os.path.splitext(pp)

        if len(ext) > 4:
            return 'decompressed'

        path, fn = os.path.split(fullpath)

        assert fn
        return fn

BaseContainer.add_container_type(GzipFileContainer)


class GzipFileProcessor(BaseProcessor):
    @classmethod
    def valid(cls, args, input_file):
        with input_file as infile:
            fd = infile.open()
            try:
                g = gzip.GzipFile(mode='r', fileobj=fd)
                g.read(256)
                g.close()
                return True
            except:
                return False

    @classmethod
    def unpack(cls, args, input_file):
        gzipa = GzipFileContainer(input_fd=input_file, job_args=args)

        yield {
            'next_func': 'hash',
            'accessor': gzipa,
            'file': gzipa.filename(),
            'path': gzipa.parent().relative_path()
        }
