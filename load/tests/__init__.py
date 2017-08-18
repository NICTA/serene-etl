from serene_load.scan import create_arguments as scan_args, ScanJob

import os
import shutil
BASE_DIR_PATH = os.path.join(os.path.dirname(__file__), 'data')
META_DIR_PATH = os.path.join(os.path.dirname(__file__), 'metadata')


def setup_package():
    print("SETUP?")
    if not os.path.exists(META_DIR_PATH):
        os.makedirs(META_DIR_PATH)
    args = scan_args().parse_args(["--base", BASE_DIR_PATH, "--meta", META_DIR_PATH])
    ScanJob(args=args)


def teardown_package():
    print("TEARDOWN?")
    if os.path.exists(META_DIR_PATH):
        print("Delete the metadata directory??")
        # shutil.rmtree(META_DIR_PATH)
    pass