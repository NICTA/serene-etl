
# REQUIRED_ABAC_FILTERS is a map of user attributes to functions that return filter query strings (or None if no filter is reqd)
from serene_metadata import REQUIRED_ABAC_FILTERS

def make_user_filters(user):
    filters = []

    for source_attribute, filter_gen in REQUIRED_ABAC_FILTERS.iteritems():

        attr = user.get_permission(source_attribute)
        flt = filter_gen(attr)
        if flt:
            if type(flt) == list:
                filters.extend(flt)
            else:
                filters.append(flt)

    return [('fq', _) for _ in filters]

