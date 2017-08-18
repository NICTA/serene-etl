import datetime
import logging
import string
import re

# normalization helpers
import pycountry
import phonenumbers
import validate_email

from pyairports.airports import Airports

from repoze.lru import LRUCache

# Fuzzy matching helper
from fuzzy import TFIDF
from schema_exceptions import *

logging.getLogger("pycountry.db").setLevel(logging.INFO)

PHONENUMBER_CACHE = LRUCache(50000)


class UTC(datetime.tzinfo):
    """
    All datetimes in SOLR must be represented in UTC
    """
    def utcoffset(self, dt):
        return datetime.timedelta(minutes=0)

    def dst(self, date_time):
        return datetime.timedelta()

    def tzname(self, dt):
        return 'Z'

utc = UTC()


class Attribute(object):
    """
    Base attribute type - TYPE defines how this is mapped into SOLR
    """
    TYPE = '_ss'


class Digits(Attribute):
    """Integer - only digits (0-9) are allowed"""

    @classmethod
    def validate(cls, base_object, value):
        if all(_ in string.digits for _ in value):
            return value
        else:
            raise SchemaAttributesInvalidDigits('"{}" contains non-digits'.format(base_object.__class__.__name__))


class PhoneNumber(Attribute):
    """phone number in E164 format - for example 6129000000 (note it has no leading + sign!)"""

    @classmethod
    def validate(cls, base_object, value):
        """validate phone number and convert to E164 format without the leading +"""

        cache_hit = PHONENUMBER_CACHE.get(value)
        if cache_hit:
            ret, country = cache_hit
            base_object.set_attr('country', country)
            return ret

        try:
            if ':' in value:
                region, number = value.split(':')
                pn = phonenumbers.parse(number, region=region)
            else:
                number = value if value.startswith('+') else '+{0}'.format(value)
                pn = phonenumbers.parse(number)
        except:
            raise SchemaAttributesInvalidPhoneNumber('"{}" is not a valid number'.format(value))

        if not phonenumbers.is_valid_number(pn):
            raise SchemaAttributesInvalidPhoneNumber('"{}" is not a valid number'.format(pn))

        country = phonenumbers.region_code_for_country_code(pn.country_code)
        ret = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)[1:]

        PHONENUMBER_CACHE.put(value, (ret, country))
        base_object.set_attr('country', country)

        return ret


class Email(Attribute):
    @classmethod
    def validate(cls, base_object, value):
        if validate_email.validate_email(value):
            return value
        raise SchemaAttributesInvalidEmailAddress(u"{} does not appear to be a valid email address".format(value))


class String(Attribute):
    """Generic string with no defined format"""
    pass


class Datestamp(Attribute):
    """ISO format date stamp in UTC - [see the readme for details](README.md#searching-for-dates)"""
    TYPE = '_dts'


class Datetimestamp(Attribute):
    """ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates)"""
    TYPE = '_dts'


def make_title_case(_):
    if len(_) > 1:
        return _[0].upper() + _[1:].lower()
    else:
        return _[0].upper()

word_split = re.compile(r'[%s\s]+' % re.escape(string.punctuation), flags=re.UNICODE)
space_remove = re.compile(r'[\W]+', flags=re.UNICODE)


class PersonName(Attribute):
    """
    If we know the "family name" or "surname" we CAPITALISE it in the label and add it as an attribute (surname)
    If we know the "given names" or "firstnames" we "Camel Case" them in the label (at the start) and add it as an attribute (givennames)
    Where we don't know which part is which we CAPITALISE everything and put it in the label and **dont add any attributes**
    """

    @classmethod
    def validate(cls, base_object, value):
        """
        Take the name in the label and split it based on Given Names SURNAME format
        only if those attributes are empty

        eg label first LAST would be converted to label First LAST and surname:last and givennames:first
        """
        try:
            givennames, surname, unknown = value
        except ValueError:
            raise SchemaBaseError('Person object must be created using the class helpers parts_unknown or parts_known')

        known = givennames or surname
        assert not (known and unknown)
        assert known or unknown

        if known:
            label = []

            if givennames and givennames.strip():
                label.extend([make_title_case(_) for _ in filter(lambda _:_.strip(), word_split.split(givennames.strip()))])
                base_object.set_attr('givennames', ' '.join(label).lower())

            if surname and surname.strip():
                surname = space_remove.sub(' ', surname).upper()
                base_object.set_attr('surname', surname.lower().strip())
                label.append(surname)

            return ' '.join(label)
        else:
            return space_remove.sub(' ', unknown).upper().strip()


class EnumType(Attribute):
    @classmethod
    def validate(cls, base_object, value):
        if value in cls.valid_types:
            return value
        else:
            raise SchemaAttributesInvalidGroupType('{} not in {}'.format(value, cls.valid_types))


class PassportType(EnumType):
    """
    Passport type (if known) can be blank or one of 'Private', 'Diplomatic', 'Official', 'PublicAffairs', 'Service'
    """
    valid_types = [
        'Private',
        'Diplomatic',
        'Official',
        'PublicAffairs',
        'Service'
    ]


class EntityGroupType(EnumType):
    """
    Reason why these entities are grouped. Must be one of: TravelBooking
    """
    valid_types = [
        'TravelBooking'
    ]


class CountryName(Attribute):
    """Full country name from ISO 3166"""
    LOOKUP = {}

    OVERRIDE = {}

    @classmethod
    def validate(cls, base_object, value):
        try:
            country = pycountry.countries.get(name=value)
        except KeyError:
            country = pycountry.historic_countries.get(name=value)

        return country.name

    @classmethod
    def best_match(cls, name, counter = None):
        """
            Find the closest country name we can using TFIDF fuzzy matching
        """

        try:
            result = cls.LOOKUP[name]

        except KeyError:

            try:
                match = cls.OVERRIDE[name]
            except KeyError:

                try:
                    match = pycountry.countries.get(name=name).name
                except KeyError:
                    match = cls.tfidf.match(name)

            cls.LOOKUP[name] = result = match

        if counter:
            counter.add(u'CountryName {} -> {}'.format(name, result))

        if not result:
            raise SchemaAttributeError

        return result


CountryName.tfidf = TFIDF(
    [_.name for _ in pycountry.countries]+[_.name for _ in pycountry.historic_countries]
)


class CountryCode(Attribute):
    """[ISO 3166 2 digit country code](countries.md)"""
    LOOKUP = {}

    @classmethod
    def best_match_from_name(cls, name, counter=None):

        try:
            result = cls.LOOKUP[name]

        except KeyError:

            country_name = CountryName.best_match(name, counter=counter)

            try:
                country = pycountry.countries.get(name=country_name)
            except KeyError:
                country = pycountry.historic_countries.get(name=country_name)

            code=country.alpha2
            cls.LOOKUP[name] = result = code

        if counter:
            counter.add(u'CountryCode {} -> {}'.format(name, result))

        return result

    @classmethod
    def from_alpha3(cls, alpha3):

        try:
            return cls.LOOKUP[alpha3]
        except KeyError:
            try:
                country = pycountry.countries.get(alpha3=alpha3)
            except KeyError:
                country = pycountry.historic_countries.get(alpha3=alpha3)
            code=country.alpha2
            cls.LOOKUP[alpha3] = code
            return code

    @classmethod
    def validate(cls, base_object, value):
        if value in cls.valid_values:
            return value
        else:
            raise SchemaAttributesInvalidCountryCode('{} not a valid country code'.format(value))
        # assert value in cls.valid_values

CountryCode.valid_values = pycountry.countries.indices['alpha2'].keys() + \
                           pycountry.historic_countries.indices['alpha2'].keys()


class geoloc(Attribute):
    FORCE_FIELD_NAME = 'geoloc'
    """
    Special Geo Location attribute

    must be called "geoloc" on the attribute of an object..

    Specified as:     lat,lon
    eg: -70.0324,170.8219

    Verify that it meets these requirements
    Encoded onto a geoloc attribute on an object and a geoloc field in solr (location_rpt field type)
    """

    @classmethod
    def validate(cls, base_object, value):
        lat, lon = value.split(',')
        lat = float(lat)
        lon = float(lon)
        if (-90.0 <= lat <= 90.0) and (-180.0 <= lon <= 180.0):
            return value
        else:
            raise SchemaAttributesInvalidGeoLocation('Invalid geolocation data')
        # assert lat >= -90.0 and lat <= 90.0
        # assert lon >= -180.0 and lon <= 180.0


airports = Airports()


class AirportIATA(Attribute):
    """Alpha3 IATA Code for airports using a [list of airports from pyairports](airports.md)"""
    @classmethod
    def validate(cls, base_object, value):
        if len(value) == 3 and airports.is_valid(value):
            return value.upper()
        else:
            raise SchemaAttributesInvalidIATA('Invalid IATA Code: {}'.format(value))


class Gender(Attribute):
    """
    Gender - either   M   or   F
    """

    @classmethod
    def validate(cls, base_object, value):
        value = value.upper()
        if value in ['M', 'F']:
            return value
        else:
            raise SchemaAttributesInvalidGender('Invalid gender value: {}'.format(value))
