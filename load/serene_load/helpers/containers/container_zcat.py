import os
from serene_load.helpers.containers.container_base import BaseContainer, BaseProcessor, TempFileContainer
import logging
import subprocess

log = logging.getLogger()


class ZCatFileContainer(TempFileContainer):
    def decompress(self, source, target):
        subprocess.check_call('gunzip -dc < "{}" > {}'.format(source, target), shell=True)

    def filename(self):
        pp = self.parent_path()

        path, _fn = os.path.split(pp)
        fn, ext = os.path.splitext(_fn)

        if len(ext) <= 3:
            return fn
        else:
            return 'decompressed'

BaseContainer.add_container_type(ZCatFileContainer)


class ZCatFileProcessor(BaseProcessor):
    @classmethod
    def valid(cls, args, input_file):

        with input_file as infile:

            fp = infile.instantiate_file()

            result = subprocess.check_output(['file', fp])

            if "compress'd data" in result:
                return True
            return False

    @classmethod
    def unpack(cls, args, input_file):

        zcat = ZCatFileContainer(input_fd=input_file, job_args=args)

        yield {
            'next_func': 'hash',
            'accessor': zcat,
            'file': zcat.filename(),
            'path': zcat.parent().relative_path()
        }
