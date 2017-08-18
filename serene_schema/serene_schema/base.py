import abc
import collections
import inspect
import random
import attributes

from serene_schema import VALID_TYPES, VALID_TRANSACTIONS
from schema_exceptions import *

# Class node data representation
object_rep = collections.namedtuple(
    'object_rep',
    field_names=[
        'type',         # Type label
        'label',        # Identifer label
        'attributes',   # Linked data nodes
        'links'         # Linked class nodes (see link_rep)
    ])

# Link representations between Class nodes and other class nodes
link_rep = collections.namedtuple(
    'link_rep',
    field_names=[
        'type',         # Link label
        'attributes',   # other attributes related to the link
        'objects',      # linked class nodes
        'reversed'      # direction
    ])


def empty_type(t):
    return inspect.getmro(t)[1] == SchemaBase


class ObjectBase(object):
    """
    Base object type
    """

    attrs = {}

    def __init__(self, attrs=None):
        self._attrs = {}

        if attrs is not None:
            for k, v in attrs.iteritems():
                self.set_attr(k, v)

    @classmethod
    def class_path(cls):
        classes = inspect.getmro(cls)
        path = [str(_.__name__) for _ in classes]
        path.reverse()
        return path[3:]

    @classmethod
    def name(cls):
        # generated at runtime - much faster than walking the class hierarchy each time
        return cls.__name__

    @classmethod
    def shared_attrs(cls):
        """
        determine which attributes are not unique (by name) across all objects
        """
        shared = set()

        for t in VALID_TYPES.union(VALID_TRANSACTIONS):
            if t == cls:
                continue
            for k, v in t.attrs.iteritems():
                if k in cls.attrs:
                    shared.add(k)

        return shared

    @classmethod
    def parent_objects(cls):
        for c in VALID_TYPES.union(VALID_TRANSACTIONS):
            if issubclass(cls, c):
                yield c

    @staticmethod
    def instantiate_attrs(_attrs):
        attrs = [(k, v) for k, v in _attrs.iteritems() if not type(v) == set]

        for k, v in ((k, v) for k, v in _attrs.iteritems() if type(v) == set):
            for _ in v:
                try:
                    attrs.append(
                        (k, _)
                    )
                except:
                    print k
                    print _
                    raise

        return attrs

    def assert_real(self):
        """
        Walk the object heirarchy ensuring there is no class objects, only class instances in _links and _attrs
        """
        if not type(self) != type:
            raise SchemaBaseInvalidObjectType('Object is not real {}'.format(self))

        try:
            for k, v in self._attrs.iteritems():
                if not type(v) != type:
                    raise SchemaBaseInvalidAttributeType('Attribute {} is not real on {}'.format(k, self))

            for k, v in self.attrs.iteritems():
                if not type(v) == type:
                    raise SchemaBaseInvalidAttributeModification('Attribute {} appears to have been modified on {} - please use set_attr() instead'.format(k, self))

        except RuntimeError as e:
            raise Exception('Loop in {}'.format(self))

    def verify_value(self, attribute, value, details, key):
        """
        Attribute values will be verified if the attribute Class object has a function called verified
        """
        assert value
        assert inspect.isclass(attribute), '{} is not a class on {} with value {}'.format(attribute, details, value)
        validate_func = getattr(attribute, 'validate', None)

        validate_name = getattr(attribute, 'FORCE_FIELD_NAME', None)
        if validate_name:
            if not key == validate_name:
                raise SchemaBaseInvalidAttribute('Attribute called {} but must be called {} {}'.format(key, validate_name, details))

        if validate_func is None:
            # no verification possible
            return value
        else:
            return validate_func(self, value)

    def set_attr(self, k, value):
        if k not in self.attrs:
            raise SchemaBaseUnknownAttribute('Unknown attribute on {} with name {}'.format(self.name(), k))

        if type(value) is not list:
            value = [value]

        for v in value:
            if not v:
                continue
            verified = self.verify_value(attribute=self.attrs[k], value=v, details='{} on {}'.format(k, self.name()), key=k)
            if k in self._attrs:
                self._attrs[k].add(verified)
            else:
                self._attrs[k] = {verified}


class SchemaBase(ObjectBase):
    """
    Extends the Object base by adding a label and link types
    """

    label = attributes.String
    links = []

    def __init__(self, label=None, attrs=None, links=None):

        ObjectBase.__init__(self, attrs=attrs)
        if label is not None:
            # a label on the class instantiation means the repr method should never generate any dummy data
            # to ensure that happens let's remove any potential attributes and links from the class properties

            self.label = self.verify_value(attribute=self.label, value=label, details=self.name(), key='label')

            self._links = []

            if links:
                self.add_links(links)

            # Must use our inheritence to intialise attributes
            self.enrich()

        else:
            random.shuffle(self.links)

    def add_links(self, links):
        for link in links:
            self.add_link(link)

    def add_link(self, link):
        if not isinstance(link, Transaction):
            raise SchemaBaseUnknownLinkType('Unknown link type on {} : {}'.format(self.name(), link))
        if not isinstance(link, tuple(self.links)):
            raise SchemaBaseLinkTypeNotSupported('Link type {} not supported on {}'.format(link, self.name()))
        self._links.append(link)

    def assert_real(self):

        ObjectBase.assert_real(self)

        for link in self._links:

            ObjectBase.assert_real(link)

            for k in link._objects:
                if not type(k) != type:
                    raise SchemaBaseInvalidLinkType('Link object {} is not real on {}'.format(k, self))

                k.assert_real()

        for link in self.links:
            if not type(link) == type:
                raise SchemaBaseInvalidLinkModification('Link type {} appears to have been added - please use .add_link instead'.format(link))

    def enrich(self):
        """
        Opportunity for objects to add attributes to themselves (eg geocoding, etc) and to add
        additional data that might not have been included originally
        """
        return

    @classmethod
    def reverse_links(cls):
        links = []
        for c in VALID_TRANSACTIONS:

            if any(map(lambda d: d == cls or issubclass(cls, d), c.links)):
                links.append(c)

        return links

    def repr(self, depth=0):
        """
        Generate the object representation
        """
        attrs = self.instantiate_attrs(self._attrs)

        return object_rep(
            self.__class__,
            self.label,
            tuple(attrs),
            tuple(self.repr_links(depth + 1)) if depth == 0 else tuple()
        )

    def repr_links(self, depth):
        """
        Walk down the link heirarchy
        """
        links = []
        for link in self._links:
            attrs = self.instantiate_attrs(link._attrs)

            objects = []
            for obj in link._objects:
                if not obj is not None:
                    raise SchemaBaseEmptyLink('None link found in {}'.format(link))
                # assert obj is not None, 'None link found in {}'.format(link)
                objects.append(obj.repr(depth=0))

            links.append(
                link_rep(
                    type=link.__class__,
                    attributes=attrs,
                    objects=objects,
                    reversed=link.reversed
                )
            )

        return links


class Transaction(ObjectBase):
    """
    Extends the ObjectBase class by adding linked objects and a reversed boolean
    """

    attrs = {
        'timestamp': attributes.Datetimestamp
    }
    links = []

    def add_objects(self, objects):
        for obj in objects:
            self.add_object(obj)

    def add_object(self, obj):
        if not isinstance(obj, SchemaBase):
            raise SchemaBaseUnknownObjectType('Unknown object on {} : {}'.format(self.name(), obj))

        self.check_direction(obj)

        self._objects.append(obj)

    @classmethod
    def reverse_links(cls):

        links = []

        for c in VALID_TYPES:

            if any(map(lambda d: d == cls or issubclass(cls, d), c.links)):
                links.append(c)

        return links

    def __init__(self, objects=None, attrs=None, reversed=False):
        self._objects = []
        self.reversed = reversed

        if not attrs:
            attrs = {}

        if objects:

            all_real = all(isinstance(obj, SchemaBase) for obj in objects)
            all_dummy = all(inspect.isclass(obj) and issubclass(obj, SchemaBase) for obj in objects)

            if all_real or all_dummy:
                pass
            else:
                raise SchemaBaseEmptyObject('All objects must be either instantiated or dummy data on {}'.format(self))

            self.add_objects(objects)
            ObjectBase.__init__(self, attrs=attrs)

    @abc.abstractmethod
    def check_direction(self, obj):
        pass


class DirectionalTransaction(Transaction):
    def check_direction(self, obj):
        if self.reversed:
            if not isinstance(obj, tuple(self.reverse_links())):
                raise SchemaBaseLinkTypeNotSupported('Link type not supported {} -{}->'.format(obj.name(), self.name()))
        else:
            if not isinstance(obj, tuple(self.links)):
                raise SchemaBaseLinkTypeNotSupported('Link type not supported: -{}-> {}'.format(self.name(), obj.name()))


class NonDirectionalTransaction(Transaction):
    def check_direction(self, obj):
        if not isinstance(obj, tuple(self.reverse_links() + self.links)):
            raise SchemaBaseLinkTypeNotSupported('Link type not supported {} -{}->'.format(obj.name(), self.name()))
