import importlib
import inspect

VALID_TYPES = set()
VALID_TRANSACTIONS = set()

from serene_schema.base import ObjectBase, SchemaBase, Transaction, NonDirectionalTransaction, DirectionalTransaction

def all_links(cls):
    """
    Each object will have the attributes declared directly on the object in the attrs dictionary. In addition there
    may be attributes declared by a particular object's parent classes. This function walks the class hierarchy to
    collect the attrs in the object's parent classes

    For example if Location.City is a subclass of Location and Location has the attribute GPS_COORDS then
    this function would combine GPS_COORDS and the existing attributes on the Location.City object and return the
    combination
    """

    links = cls.links[:]

    # walk the class hierarchy
    for sub in inspect.getmro(cls):

        for link in getattr(sub, 'links', []):

            if link in links:
                continue
            links.append(link)

    return links


def all_attributes(cls):
    """
    Each object will have the attributes declared directly on the object in the attrs dictionary. In addition there
    may be attributes declared by a particular object's parent classes. This function walks the class hierarchy to
    collect the attrs in the object's parent classes

    For example if Location.City is a subclass of Location and Location has the attribute GPS_COORDS then
    this function would combine GPS_COORDS and the existing attributes on the Location.City object and return the
    combination
    """

    attrs = cls.attrs.copy()

    # walk the class hierarchy
    for sub in inspect.getmro(cls):

        for name, prop in getattr(sub, 'attrs', {}).iteritems():

            if name in attrs:
                continue
            attrs[name] = prop

    return attrs

__all__ = [
    'accounts',
    'attributes',
    'documents',
    'entities',
    'events',
    'locations',
    'objects',
    'transactions'
]



def polymorphic_setup(all, module_name='serene_schema'):

    for mname in all:

        module = importlib.import_module('.' + mname, module_name)

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                if issubclass(obj, ObjectBase) and obj not in [ObjectBase, SchemaBase, Transaction]:
                    obj.attrs = all_attributes(obj)
                    # obj.links = all_links(obj)

                    if issubclass(obj, SchemaBase):
                        VALID_TYPES.add(obj)
                    elif obj in [Transaction, NonDirectionalTransaction, DirectionalTransaction]:
                        pass
                    elif issubclass(obj, (NonDirectionalTransaction, DirectionalTransaction)):
                        assert obj.links is not Transaction.links, \
                            'Transaction {} should be defined with links = [...'.format(obj)
                        VALID_TRANSACTIONS.add(obj)

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                if issubclass(obj, NonDirectionalTransaction):

                    a = set(obj.links)

                    for _ in obj.reverse_links():
                        try:
                            if obj in _.links:
                                a.add(_)
                        except ValueError:
                            pass

                    for _ in obj.links:
                        if obj not in _.links:
                            _.links.append(obj)

                    obj.links = list(a)

polymorphic_setup(__all__)
