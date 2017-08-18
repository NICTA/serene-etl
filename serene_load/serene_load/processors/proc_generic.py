import logging
import io
from collections import Counter, defaultdict
import binascii
import re
from itertools import chain, islice, izip_longest
from functools import partial
import base64

from serene_load.helpers.load_helpers import JobProcessor

log = logging.getLogger()

MAX_SEP_LEN = 3  # Try to find separators upto a certain length
MAX_LINE_LEN = 1024 * 1024 * 1024

QUOTED_SPLIT_RE = r'(?:^|{d})(?:=[^{q}]|({q})?){q}?((?(1)[^{q}]*|[^{d}{q}]*)){q}?(?={d}|$)'


def remove_quotes(s):
    """
    Where a string starts and ends with a quote, remove the quote
    """
    if len(s) > 1 and s[0] == s[-1] and s[0] in ['"', "'"]:
        return s[1:-1]
    return s


def proc_line(_line, field_names, split_line):
    line = _line.strip()
    line_len = len(line)

    if line_len == 0:
        return 'Zero length line', None
    elif line_len > MAX_LINE_LEN:
        return 'Line > 1mb', None

    cells = dict(izip_longest(field_names, split_line(_line)))

    # we expect each row to have the same number of cells as the header...
    if len(cells) != len(field_names):
        return 'expecting {} cells but got {}'.format(len(field_names), len(cells)), None

    # add the row number and base details from the source file to the output cells
    return None, cells


def find_ngrams(word, n):
    return [''.join(_) for _ in zip(*[word[i:] for i in range(n)])]


def detect_noquote_separator(lines):
    """
    Detect separators assuming the separator is not used anywhere else and a constant number of columns

    Pseudo logic is as follows:

    1. Calculate frequencies of all n-grams for the lines passed to the function
    2. For top x n-grams, find the first that results in consistent number of columns across the sample
    """
    possible_seps = Counter()
    for line in lines:
        for sl in range(1, MAX_SEP_LEN + 1):
            for ngram in find_ngrams(line.strip(), sl):
                possible_seps[ngram] += 1

    lengths = defaultdict(dict)

    for psep, count in possible_seps.iteritems():
        lengths[len(psep)][psep] = count

    for length, separators in sorted(lengths.iteritems(), key=lambda k: k[0], reverse=True):
        log.debug('trialling {} separators of length {}'.format(len(separators), length))

        for psep, count in sorted(separators.iteritems(), key=lambda k: k[1], reverse=True):

            columns = Counter()

            for line in lines:
                columns[len(line.split(psep))] += 1

            if len(columns) == 1:
                return psep
            elif len(columns) < 4:
                log.debug(u'sep "{}" created {} columns'.format(psep, len(columns)))

    return None


def regex_splitter(pattern, line):
    return [m.groups()[1].strip() for m in pattern.finditer(line)]


def plain_splitter(sep, line):
    return [remove_quotes(_.strip()) for _ in line.strip().split(sep)]


class Generic(JobProcessor):
    """Generic process that processes delimited data with a single line header

    Assumes that each row contains the same number of columns as the header
    Assumes that the specified separator does not appear within a cell
    """
    FILTERS = [
        'mime=text/.*',
        '!est_lines=0'
    ]

    @staticmethod
    def process_file(args, meta, fd):
        enc = args.__dict__.get('enc', meta.get('enc', 'utf-8'))
        text_io_args = {
            'encoding': enc,
            'errors': 'replace',
            'newline': args.__dict__.get('lineend')
        }

        fd = io.TextIOWrapper(buffer=fd, **text_io_args)

        sample = list(islice(fd, 1000))
        header_row = sample[0]

        sep = args.__dict__.get('sep')
        if not sep:
            sep = detect_noquote_separator(sample)

        assert sep, 'No separator detected / specified'
        log.debug('Using separator "{}" ({})'.format(sep, binascii.b2a_hex(sep)))

        quotechar = args.__dict__.get('quotechar')
        if quotechar:
            pattern = re.compile(QUOTED_SPLIT_RE.format(d=re.escape(sep), q=quotechar))
            line_splitter = partial(regex_splitter, pattern)
        else:
            line_splitter = partial(plain_splitter, sep)

        header_sep = args.__dict__.get('header_sep', sep)
        field_names = plain_splitter(header_sep, header_row.lower())

        log.debug("Found field names: {0}".format(field_names))

        col_count = len(line_splitter(sample[1]))
        assert len(field_names) == col_count, "Number of fields in first line does not match number of fields in header"

        for row_num, line in enumerate(chain(sample[1:], fd), 1):

            error, r = proc_line(line, field_names, line_splitter)
            if not error:
                args.error_counter('LINE OKAY')
                yield r
            else:
                args.error_counter(error)
                yield {
                    '_load_error': error,
                    '_line_b64encoded': base64.b64encode(line.encode(enc)), #undo the encoding before dumping as b64
                    'row': row_num
                }

