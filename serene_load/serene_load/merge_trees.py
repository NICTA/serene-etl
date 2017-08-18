import logging
import argparse
from serene_load.meta_select import load_meta


def create_arguments():
    parser = argparse.ArgumentParser(description='take all json data from one directory and merge into another tree')
    parser.add_argument('--meta', type=unicode, help='Directory containing primary metadata', required=True)
    parser.add_argument('--source', type=unicode, help='Directory containing secondary metadata to merge into primary', required=True)
    parser.add_argument('--verbose', type=bool)


def setup_logging(LEVEL):
    logger = logging.getLogger()
    logger.setLevel(LEVEL)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(LEVEL)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    return logger


def main():
    parser = create_arguments()
    args = parser.parse_args()
    log = setup_logging(LEVEL=logging.DEBUG if args.debug is True else logging.INFO)

    primary = load_meta(args.meta)
    secondary = load_meta(args.source)

    print secondary

if __name__ == '__main__':
    main()
