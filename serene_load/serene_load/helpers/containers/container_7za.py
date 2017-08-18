from serene_load.helpers.containers.container_base import TempFileContainer, BaseContainer, BaseProcessor
import logging
import datetime
import io
import re
import subprocess

log = logging.getLogger()


class SevenZipFileContainer(TempFileContainer):
    def decompress(self, source, target):
        subprocess.check_call("/usr/bin/7za e '{}' '{}' -so > {}".format(source, self.filename(), target), stderr=io.open('/dev/null', 'w'), shell=True)

BaseContainer.add_container_type(SevenZipFileContainer)

with_dt = re.compile(
    r'(?P<year>[\d]{4})-(?P<month>[\d]{2})-(?P<day>[\d]{2}) (?P<hour>[\d]{2}):(?P<minute>[\d]{2}):(?P<second>[\d]{2}) [^\s]{5}[\s\t]+(?P<size>[\d]+)[\s\t\d]+[\s]+(?P<name>.*)$',
)

no_dt = re.compile(
    r'^[\s]+[^\s]{5}[\s\t]+(?P<size>[\d]+)[\s\t\d]+[\s]+(?P<name>.*)$',
)

class SevenZipFileProcessor(BaseProcessor):
    @classmethod
    def valid(cls, args, input_file):
        with input_file as infile:
            fp = infile.instantiate_file()
            try:
                subprocess.check_call(u'7za l "{}" >& /dev/null'.format(fp), shell=True)
                return True
            except subprocess.CalledProcessError:
                return False

    @classmethod
    def unpack(cls, args, input_file):
        with input_file as infile:
            fp = infile.instantiate_file()
            log.debug(u'using {} for {}'.format(fp, input_file))

            output = subprocess.check_output(u"7za l '{}'".format(fp), shell=True)
            file_listing = False
            for line in output.split('\n'):
                if file_listing:
                    if line.startswith('----'):
                        file_listing = False
                        continue
                    if line[4] == '-':
                        match = with_dt.match(line)
                        mtime = datetime.datetime(
                            year=int(match.group('year')),
                            month=int(match.group('month')),
                            day=int(match.group('day')),
                            hour=int(match.group('hour')),
                            minute=int(match.group('minute')),
                            second=int(match.group('second')),
                        ).isoformat()[:19]
                    else:
                        mtime = None
                        match = no_dt.match(line)

                    if match is None:
                        raise Exception(line)

                    filename = match.group('name').strip()
                    assert not filename == 'file'

                    sz = SevenZipFileContainer(input_fd=input_file, file=filename, job_args=args)

                    d = {
                        'next_func': 'hash',
                        'accessor': sz,
                        'file': filename,
                        'path': input_file.relative_path()
                    }

                    if mtime:
                        d.update({
                            'mtime': mtime
                        })
                    yield d

                else:
                    if line.startswith('----'):
                        file_listing = True
