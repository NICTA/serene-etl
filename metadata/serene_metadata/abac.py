
# SOLR Standard Query Parser
# Boolean Operators
# AND / && - Requires both terms on either side of the operator to be present
# NOT / !  - requires that the following term not be present
# OR / ||  - requires that either term (or both terms) be present for a match
# we apply these in the fq part of the query which is AND between terms by default

# These helpers make it easier to specify ABAC rules on specific fields...

def solr_mkfilter(spec, fld, value):
    """
    based on a "spec" (see examples below) construct the actual
    filter query - depending on whether it requires a list or a single value

    Filters are returned as a list with each item in the list being added to fq= (see serene_proxy repo)
    """
    if type(value) == list:
        return ' '.join(spec.format(fld, _) for _ in value)
    else:
        return spec.format(fld, value)


def solr_deny_all(fld, values):
    """
    require that no documents containing any of field:value are present in the result set
    """
    spec = '-{}:{}'
    return solr_mkfilter(spec, fld, values)

def solr_require_one(fld, values):
    """
    require that only documents that contain at least one field:value are present in the result set
    """
    spec = '{}:{}'
    return solr_mkfilter(spec, fld, values)

def solr_require_all(fld, values):
    """
    require that only documents that contain all field:value are present in the result set
    """
    spec = '+{}:{}'
    return solr_mkfilter(spec, fld, values)

