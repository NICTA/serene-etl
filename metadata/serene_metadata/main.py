
import json
from serene_metadata import DEFINED_FIELDS_DICT

def main():
    fields = {}
    for name, f in DEFINED_FIELDS_DICT.iteritems():

        fields[name] = dict(
            MULTIVALUED = f.MULTIVALUED,
            PROXY_STATS = f.PROXY_STATS,
            TYPE = f.TYPE,
            REQUIRED_AT_INDEX = f.REQUIRED_AT_INDEX,
            REQUIRED_AT_LOAD = f.REQUIRED_AT_LOAD,
            DESC = f.__doc__.strip()
        )


    print json.dumps(fields, indent=1, sort_keys=True)

if __name__ == '__main__':
    main()