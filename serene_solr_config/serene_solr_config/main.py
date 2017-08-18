import io
import os
import shutil
import argparse

from pkg_resources import resource_filename, resource_string


from serene_metadata import DEFINED_FIELDS_DICT


def gen_patch(lines):
    data = [
        '212,{}d188'.format(212 + len(lines) - 1)
    ]

    data.extend(
        map(
            lambda _:u'<     {}'.format(_), lines
        )
    )

    return u'\n'.join(data)

def gen_line(name, type, required, multi):
    return u'<field name="{}" type="{}"   indexed="true" stored="true" required="{}" multiValued="{}" docValues="true"/>'.format(name, type, required, multi)



def create_arguments():
    """
        Parse arguments to solr config
    """
    parser = argparse.ArgumentParser(prog='solr_config', add_help=False, description='Generate SOLR Configuration')

    parser.add_argument('--version', metavar='solr_version', help='Which SOLR version to use', required=False, default='6.0.0')
    parser.add_argument('--config', metavar='solr_config', help='Which SOLR config to use as the template', required=False, default='data_driven_schema_configs')
    parser.add_argument('--output', metavar='output_dir', help='Where to place the output', required=False, default='solr_config')

    return parser


def make_config(_output, _version, _config):

    fields = map(lambda _:gen_line(
        _[0],
        _[1].TYPE,
        str(_[1].REQUIRED_AT_INDEX or _[1].REQUIRED_AT_LOAD).lower(),
        str(_[1].MULTIVALUED).lower()
    ), DEFINED_FIELDS_DICT.iteritems())

    for _ in fields:
        print _

    output = os.path.normpath(_output)

    if os.path.exists(output):
        raise ValueError('Output path "{}" already exists'.format(output))

    configset_path = resource_filename('serene_solr_config','data/solr-distributions/solr-{}/configsets/{}/conf/'.format(_version, _config))
    shutil.copytree(configset_path, _output)

    managed = resource_string('serene_solr_config', 'data/managed-schema.patch')

    managed = managed.replace('CUSTOM_FIELDS_INSERTED_HERE', gen_patch(fields))

    with io.open(os.path.join(_output, 'managed-schema.patch'), 'w') as mspo:
        mspo.write(managed)

    shutil.copy(
        resource_filename('serene_solr_config', 'data/solrconfig.patch'),
        os.path.join(_output, 'solrconfig.patch')
    )

    shutil.copy(
        resource_filename('serene_solr_config', 'data/apply_patch.sh'),
        os.path.join(_output, '..', 'apply_patch.sh')
    )



def main():
    parser = create_arguments()
    args = parser.parse_args()
    make_config(
        _output= args.output,
        _version = args.version,
        _config = args.config
    )

if __name__ == '__main__':
    main()
