"""

Documents, paper, etc

"""

import base, attributes, transactions

class IssuedDocument(base.SchemaBase):
    """Issued documents base type"""
    links = [
        transactions.AssociatedWith,
        transactions.Travelled

    ]
    attrs = {
        'issued': attributes.Datestamp,
        'expiry': attributes.Datestamp,
        'country': attributes.CountryCode
    }

transactions.Holds.links.append(IssuedDocument)
transactions.AssociatedWith.links.append(IssuedDocument)

class Passport(IssuedDocument):
    """A passport is a type of ID issued for travel purposes between countries"""
    attrs = {
        'type': attributes.PassportType
    }

class Visa(IssuedDocument):
    attrs = {
        'class': attributes.String,
        'application': attributes.Datestamp
    }
