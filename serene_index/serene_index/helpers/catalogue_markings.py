import json
import os

from serene_metadata import CATALOGUE_MAPPINGS, REQUIRED_INDEX_FIELDS, REQUIRED_LOAD_FIELDS


def load_markings(scandir):
    catalogue = {}

    for path, dir, files in os.walk(scandir):
        for fn in files:
            if fn.endswith('.json'):
                cid, _fn = fn.split('.')
                with open(os.path.join(path, fn), 'r') as inmark:
                    catalogue[int(cid)] = json.load(inmark)

    return catalogue


def get_markings(catalogue_dir, cid, result):
    """
    Take a directory of catalogue entries and extract the specific metadata related to CID

    Add it to fields as defined in serene_metadata
    """

    catalogue = load_markings(os.path.normpath(catalogue_dir))

    catalogue_markings = catalogue[cid]

    for catalogue_entry, serene_field in CATALOGUE_MAPPINGS.iteritems():

        if catalogue_entry in catalogue_markings:

            if type(catalogue_markings[catalogue_entry]) is list:

                values = [
                    serene_field.catalogue_map(_)
                    for _ in catalogue_markings[catalogue_entry]
                ]

            else:

                values = [
                    serene_field.catalogue_map(catalogue_markings[catalogue_entry])
                ]

            #remove any None values
            values = filter(lambda _:_ is not None, values)

            if values:
                result[serene_field.name()] = serene_field.validate_final(values)

    for field in REQUIRED_INDEX_FIELDS:
        if field in REQUIRED_LOAD_FIELDS:
            #if it was required at the LOAD stage we don't test for it here - we test for it in the record_builder
            continue
        assert field in result, '"{}" is required at the index step but was not present in this catalogue entry {}'.format(field, cid)

    return result
