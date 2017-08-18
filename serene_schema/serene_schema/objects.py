"""

Physical objects - could be things like computers, vehicles, phones, etc

"""


import base, transactions


class Object(base.SchemaBase):
    """A physical object that could be located somewhere"""

    links = [
        transactions.Located
    ]


