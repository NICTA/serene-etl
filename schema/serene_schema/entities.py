"""

People, organisations


"""

from . import base, attributes, transactions

class Unknown(base.SchemaBase):
    """Unknown type used where no modelled data at all can be found"""
    pass

class Entity(base.SchemaBase):
    """Generic entity type used where a more specific type does not exist"""
    links = [
        transactions.MemberOf,
        transactions.Holds,
        transactions.AssociatedWith,
        transactions.Located,
        transactions.Travelled,
    ]


class Organisation(Entity):
    """
    An entity that is not a natural person
    """
    label = attributes.String

transactions.MemberOf.links.append(Organisation)

class Group(Entity):
    """
    A group of entities
    """
    attrs = {
        'type': attributes.EntityGroupType
    }

transactions.MemberOf.links.append(Group)

class Person(Entity):
    """
    A natural person
    """
    label = attributes.PersonName

    @classmethod
    def parts_known(cls, givennames, surname, attrs=None, links=None):
        """
        Helper function where we know the difference between given names and surnames
        """
        return cls(
            (
                givennames,
                surname,
                None
            ),
            attrs=attrs,
            links=links
        )

    @classmethod
    def parts_unknown(cls, label, attrs=None, links=None):
        """
        helper function where we dont know the difference
        """
        return cls(
            label=(
                None,
                None,
                label
            ),
            attrs=attrs,
            links=links
        )

    attrs = {
        'dob': attributes.Datestamp,
        'pob': attributes.CountryCode,
        'gender': attributes.Gender,
        'surname': attributes.String,
        'givennames': attributes.String
    }
