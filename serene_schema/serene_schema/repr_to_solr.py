import json
import datetime
import itertools
from . import base

def solr_dt_format(k):
    return k.isoformat()[:19] + 'Z'

def solr_type(value):
    #current schema only support strings, datestamps, integers, booleans and doubles

    if isinstance(value, basestring):
        return '_ss'

    if isinstance(value, datetime.datetime):
        return '_dts'

    if isinstance(value, int):
        return '_is'

    if isinstance(value, (float)):
        return '_ds'

    raise Exception('Unknown type {}'.format(type(value)))


import inspect
class SOLREncoder(json.JSONEncoder):

    def default(self, o):

        if isinstance(o, datetime.datetime):
            return solr_dt_format(o - o.utcoffset())

        elif isinstance(o, set):
            return [SOLREncoder.default(self,_) for _ in list(o)]

        elif isinstance(o, basestring):
            return o

        elif isinstance(o, base.ObjectBase):
            return o.name()

        return json.JSONEncoder.default(self, o)





def add_attribute(base, key, value):

    if type(value) == set:
        _type = map(lambda t:solr_type(t), value)
        assert len(set(_type)) == 1
        _type = _type[0]

    else:
        _type = solr_type(value)

    if key.endswith('geoloc'):
        _type = ''

    if type(value) == set:
        try:
            base[key + _type].update(value)
        except KeyError:
            base[key + _type] = value.copy()

    else:
        try:
            base[key + _type].add(value)
        except KeyError:
            base[key + _type] = {value}

    if key[0].isupper() and '.' not in key and 'geoloc' not in key:
        base['object_types'].add(key)
    else:
        base['attr_types'].add(key)

def add_attributes(base, attrs):
    for k, v in attrs:
        add_attribute(base, k, v)

def add_obj_attributes(base, obj, attrs):

    shared = obj.shared_attrs()

    for k,v in attrs:
        if k in shared:
            add_attribute(
                base,
                '{}.{}'.format(obj.name(), k),
                v
            )

def flatten(base, repr):
    """
    walk the heirarchy adding objects and attributes and link types
    """

    #add object label
    try:
        add_attribute(base, repr.type.name(), repr.label)
    except:
        # print repr.type.name()
        # print repr.label
        raise

    #add object attributes
    add_attributes(base, repr.attributes)

    #object.attributes
    add_obj_attributes(base, repr.type, repr.attributes)

    #add parent object label and attributes
    for parent_object in repr.type.parent_objects():
        #label
        add_attribute(base, parent_object.name(), repr.label)
        #attributes
        add_obj_attributes(base, parent_object, repr.attributes)
        # print parent_objects

    for link in repr.links:

        base['link_types'].add(link.type.name())

        add_attributes(base, link.attributes)
        add_obj_attributes(base, link.type, link.attributes)

        for obj in link.objects:

            flatten(base, obj)

def repr_compactor(o):

    if isinstance(o, base.link_rep):

        return (
            '{}{}'.format('-' if o.reversed else '', o.type.name()),
            o.attributes,
            [repr_compactor(_) for _ in o.objects]
        )

    elif isinstance(o, base.object_rep):
        return (
            o.type.name(),
            o.label,
            o.attributes,
            [repr_compactor(_) for _ in o.links]
        )
    else:
        return o


def repr_to_solr(repr, base=None):

    if base is None:
        base={}

    base.update({
        'object_types': set(),
        'link_types': set(),
        'attr_types': set()
    })

    flatten(base, repr)

    for k in base.keys():
        assert k in base, '{} not in {}'.format(k, base)
        base[k] = json.loads(json.dumps(base[k], cls=SOLREncoder, ensure_ascii=False), encoding='utf8')

    base['data'] = json.dumps(repr_compactor(repr), ensure_ascii=False, sort_keys=True, separators=(',',':'), cls=SOLREncoder)
    # base['data'] = repr_compactor(repr)

    return base


def make_json(record):
    return json.dumps(record, ensure_ascii=False, sort_keys=True, cls=SOLREncoder, separators=(',',':'))


# def enrichments(repr, e = None):
#
#     if e is None:
#         e = collections.defaultdict(set)
#
#     assert getattr(repr, 'enriched') is not None
#
#     for k, v in repr.enriched.iteritems():
#         types = set([solr_type(_) for _ in v])
#         assert len(types) == 1, repr.label
#         key = k + list(types)[0]
#         e[key] = e[key].union(v)
#
#     for link in repr.links:
#         if generated(link):
#             continue
#         for obj in link.objects:
#             enrichments(obj, e)
#
#     return e

