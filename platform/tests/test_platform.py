from nose.tools import *


def which(program):
    """
    Returns the full file path to a command, if found on PATH

    :param program: program to search for on PATH
    :return: file path to program if found, else None
    """
    import os

    def is_exe(path_to_file):
        return os.path.isfile(path_to_file) and os.access(path_to_file, os.X_OK)

    dir_path, file_name = os.path.split(program)
    if dir_path:
        if is_exe(program):
            return program
    else:
        for path_dir in (path.strip('"') for path in os.environ['PATH'].split(os.pathsep)):
            exe_file = os.path.join(path_dir, program)
            if is_exe(exe_file):
                return exe_file

    return None


def test_commands_available():
    assert_is_not_none(which('pyairports'))
    assert_is_not_none(which('serene_metadata'))
    assert_is_not_none(which('serene_index'))
    assert_is_not_none(which('serene_scan'))
    assert_is_not_none(which('serene_load'))
    assert_is_not_none(which('serene_proxy'))
    assert_is_not_none(which('serene_solr_config'))


def test_imports():
    try:
        import postal
        import pycountry
        import phonenumbers
        import twisted
    except ImportError as ie:
        postal = pycountry = phonenumbers = twisted = None
        assert False, "Could not import dependency: {0}".format(ie.message)
