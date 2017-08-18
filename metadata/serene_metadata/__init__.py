import inspect
import importlib
import random

__all__ = [
    'fields'
]

def validate_field(field):

    if getattr(field, 'MAP_FROM_CATALOGUE', None) is not None:
        try:
            field.catalogue_map('test')
        except NotImplementedError:
            raise
        except:
            pass

def get_fields_dict():

    fields = dict()
    module = importlib.import_module('serene_metadata.fields')
    smf = module.__dict__['SereneMetaField']

    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, smf) and obj != smf:
            try:
                validate_field(obj)
            except Exception as e:
                raise Exception('{} did not pass validation - {}'.format(name, type(e)))
            fields[obj.name()] = obj

    return fields

DEFINED_FIELDS_DICT = get_fields_dict()

# Fields required for ABAC in the serene_proxy and the ABAC business logic for that field
REQUIRED_ABAC_FILTERS = {
    _.ABAC: _.abac for _ in filter(
        lambda field: getattr(field, 'ABAC', None) is not None,
        DEFINED_FIELDS_DICT.itervalues()
    )
}

# A list of metadata fields required at the load step
REQUIRED_LOAD_FIELDS = frozenset(
    map(lambda _:_.name(),
        filter(
            lambda _: getattr(_, 'REQUIRED_AT_LOAD', False),
            DEFINED_FIELDS_DICT.itervalues()
        )
    )
)

# A list of metadata fields required at the index step
REQUIRED_INDEX_FIELDS = frozenset(
    map(lambda _:_.name(),
        filter(
            lambda _: getattr(_, 'REQUIRED_AT_INDEX', False),
            DEFINED_FIELDS_DICT.itervalues()
        )
    )
)

# Catalogue mappings to add at the index stage


# Fields required for ABAC in the serene_proxy and the ABAC business logic for that field
CATALOGUE_MAPPINGS = {
    _.MAP_FROM_CATALOGUE:_ for _ in filter(
        lambda field: getattr(field, 'MAP_FROM_CATALOGUE', None) is not None,
        DEFINED_FIELDS_DICT.itervalues()
    )
}

# Primary ID is required in the LOAD step to identify a record from a source system -
# for example, the default defined Primary ID is src_file_rec in serene_metadata.fields and serene_load.load_helpers
def get_primary_id():

    pid = None
    count = 0

    for field in DEFINED_FIELDS_DICT.itervalues():
        if getattr(field, 'PRIMARY_ID', False):
            pid = field
            count += 1

    assert count == 1, 'Exactly one PRIMARY_ID field must be defined'
    return pid

PRIMARY_ID = get_primary_id()

# Catalogue ID is required in every step to identify a dataset from your data catalogue
# for example, the default defined Catalogue ID is src_file_cid in serene_metadata.fields and serene_load.load_helpers
def get_catalogue_id():

    pid = None
    count = 0

    for field in DEFINED_FIELDS_DICT.itervalues():
        if getattr(field, 'CATALOGUE_ID', False):
            pid = field
            count += 1

    assert count == 1, 'Exactly one CATALOGUE_ID field must be defined'
    return pid

CATALOGUE_ID = get_catalogue_id()


def validate_and_remove_metadata_during_record_index(data):

    out = {}

    for key in data.keys():
        if key in DEFINED_FIELDS_DICT:
            out[key] = DEFINED_FIELDS_DICT[key].validate_final(data.pop(key))

    for key in REQUIRED_INDEX_FIELDS.union(REQUIRED_LOAD_FIELDS):
        assert key in out, 'Field "{}" was required but was not present in metadata'.format(key)

    return out


def generate_example_metadata():

    out = {}

    for name, field in DEFINED_FIELDS_DICT.iteritems():

        example = field.example()
        assert example is not None
        out[name] = example

    return out





