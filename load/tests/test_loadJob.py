from serene_load.load import create_arguments as load_args, LoadJob

import os.path
BASE_DIR_PATH = os.path.join(os.path.dirname(__file__), 'data')


def test_scan():
    print("This test should be checking if the metadata directory was created during setup")
    assert True


def test_load():
    args = load_args().parse_args(["--base", BASE_DIR_PATH, "--cid", "1", "--processor", "generic"])
    print args
    # load = LoadJob(args=args)
