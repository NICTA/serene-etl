#!/bin/bash

import os
import argparse


def create_arguments():
    parser = argparse.ArgumentParser(description='wrap directories')
    parser.add_argument('--base', type=unicode, help='Base path to scan', required=True)
    parser.add_argument('--subdir', type=unicode, help='Subdirectory of interest')
    parser.add_argument('--args', type=unicode, help='Subdirectory of interest')
    return parser


def main():
    parser = create_arguments()
    args = parser.parse_args()

    args.base = os.path.normpath(args.base)
    try:
        scandir = os.path.normpath(os.path.join(args.base, args.subdir))
    except AttributeError:
        scandir = os.path.normpath(os.path.join(args.base))

    assert os.path.exists(scandir), '{} does not exist'.format(scandir)

    for dirpath, dirnames, filenames in os.walk(scandir):
        if dirpath != scandir:
            break

        for dirname in dirnames:
            fp = os.path.join(dirpath, dirname)

            head = fp
            parts = []

            while head != args.base:
                head, tail = os.path.split(head)
                parts.append(tail)

            parts.reverse()
            subdir = os.path.join(*parts)
            print 'python scan.py --base {} --subdir {}'.format(args.base, subdir)

if __name__ == '__main__':
    main()
