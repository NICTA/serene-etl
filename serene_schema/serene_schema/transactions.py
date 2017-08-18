"""

How objects are linked (transactions are another name for "edges")

"""

from base import DirectionalTransaction, NonDirectionalTransaction

class AssociatedWith(NonDirectionalTransaction):
    """
    AssociatedWith implies a known association
    """
    links = []

class Travelled(DirectionalTransaction):
    """
    A person or passport travelled on a flight
    """
    links = []

class MemberOf(DirectionalTransaction):
    """
    A entity is a member of another entity
    """
    links = []

class Holds(DirectionalTransaction):
    """
    A entity holds a document
    """
    links = []

class Departed(DirectionalTransaction):
    """
    A flight departed ABC
    """
    links = []

class Located(DirectionalTransaction):
    """Generic location link"""
    links = []

class Arrived(DirectionalTransaction):
    """
    A flight arrived ABC
    """
    links = []

class IssuedTo(DirectionalTransaction):
    """ Documents are issued to people
    """
    links = []

class IssuedBy(DirectionalTransaction):
    """
    Documents are issued by organisations or countries
    """
    links = []

