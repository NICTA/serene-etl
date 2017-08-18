from nose.tools import *

import json


import serene_metadata


def test_metadata():

    assert serene_metadata.DEFINED_FIELDS_DICT
    assert serene_metadata.CATALOGUE_ID
    assert serene_metadata.CATALOGUE_MAPPINGS
    assert serene_metadata.PRIMARY_ID
    assert serene_metadata.REQUIRED_INDEX_FIELDS
    assert serene_metadata.REQUIRED_ABAC_FILTERS
    assert serene_metadata.REQUIRED_LOAD_FIELDS

