from . import base, attributes, transactions, entities, documents


class Account(base.SchemaBase):
    """Account base type - accounts can be associated with entities"""
    links = [
        transactions.AssociatedWith
    ]

transactions.AssociatedWith.links.append(Account)


class PhoneNumber(Account):
    """Raw phone number - no normalisation of the phone number is implied"""
    label = attributes.Digits


class Email(Account):
    """ An email address - typically in the user@domain.tld format """
    label = attributes.Email


class ITUE164(PhoneNumber):
    """Normalised phone number using ITU E164 format."""
    label = attributes.PhoneNumber

    @classmethod
    def known_region(cls, country_code, label, attrs=None, links=None):
        """ Helper function for creating an ITU E164 from a known region """
        return cls(
            label=(
                '{}:{}'.format(country_code, label)
            ),
            attrs=attrs,
            links=links
        )

    attrs = {
        'country': attributes.CountryCode
    }


class OnlineAccount(Account):
    """ An online account - unique identifier (label) for a particular online platform """

    attrs = {
        'platform': attributes.String
    }