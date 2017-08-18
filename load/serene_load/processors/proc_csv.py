from backports import csv
import logging
import io
from itertools import count
import re

from serene_load.helpers.load_helpers import JobProcessor

log = logging.getLogger()


# Pattern to remove leading or trailing whitespace or quotes
clean_pattern = re.compile('''(^[\s'"]*)|([\s'"]*$)''')


def clean_values(record):
    # n.b. Make a copy of keys as we're changing the original record (possibly deleting keys)
    for k in record.keys():
        v = clean_pattern.sub('', record[k])
        if not v:
            del record[k]
    return record


class Csv(JobProcessor):
    """Processor specifically made for CSVs
    """
    FILTERS = [
        'mime=text/.*',
        #'file=.*\.(csv|psv|tsv)$',
        '!est_lines=0'
    ]

    @staticmethod
    def process_file(args, meta, fd):
        text_io_args = {
            'encoding': args.__dict__.get('enc', meta.get('enc', 'utf-8')),
            'errors': 'replace',
            'newline': args.__dict__.get('lineend')
        }

        fd = io.TextIOWrapper(buffer=fd, **text_io_args)

        csv_args = {
            'delimiter': unicode(args.__dict__.get('delimiter', ',')),
            'quotechar': unicode(args.__dict__.get('quotechar', '"'))
        }
        log.debug("Using CSV Args: {0}".format(csv_args))

        errors = 0
        udr = csv.DictReader(fd, **csv_args)
        udr.fieldnames = [f.lower() for f in udr.fieldnames]
        log.debug("Field names found: {0}".format(udr.fieldnames))
        row_counter = count(start=1)
        for row_num in row_counter:
            try:
                record = next(udr)
                if record is None:
                    log.warn("Finished at {0}".format(row_num))
                    break
                record = clean_values(record)
                record['src_file_row'] = row_num
                yield record
            except StopIteration:
                log.warn("SI at line {0}".format(row_num))
                break
            except Exception as e:
                log.debug("Exception on line {1}: {0}".format(e.message, row_num))
                yield {"_load_error": e.message, 'src_file_row': row_num}
                errors += 1

        if errors:
            log.error('{} errors encountered in file'.format(errors))
