"""

Locations

"""

import base, transactions, attributes
import pycountry
import re

try:
    from postal.parser import parse_address
    from postal.expand import expand_address
except ImportError:
    print 'WARNING - Unable to import libpostal'
    parse_address = None
    expand_address = None

from collections import defaultdict
from pyairports.airports import Airports
from schema_exceptions import SchemaAttributesInvalidIATA
airports = Airports()


class Location(base.SchemaBase):
    """Base location type"""
    links = [
        transactions.Located
    ]
    attrs = {
        'geoloc': attributes.geoloc
    }

transactions.Located.links.append(Location)
transactions.AssociatedWith.links.append(Location)

class Country(Location):
    """ """

    label = attributes.CountryName
    attrs = {
        'country': attributes.CountryCode
    }

    def enrich(self):

        country = pycountry.countries.get(name=self.label)
        self.set_attr('country', country.alpha2)


class Address(Location):
    """A street address

    We try to do a couple of things with "Addresses".

        1. Where we can figure out the state, country and postcode, move them into attributes instead of the label
        2. Parse the rest of the label and add expansions so that searches will match common variations eg st -> street, etc
        3. Format the label as Street Address, Suburb, (City District) City if possible

    """

    label = attributes.String


    attrs = {
        'state': attributes.String,
        'state_district': attributes.String,
        'postcode': attributes.String,
        'country': attributes.CountryCode,
    }



    @staticmethod
    def clean_address(label):
        label = re.sub('\s\s+',' ',label)
        label = re.sub(',\s+,+',',',label).strip()
        while label.endswith(','):
            label = label[:-1]
        return label

    def enrich(self):
        """
        format address label consistenty if possible and remove postcode and country...
        """
        # values = {
        #     'house': '',
        #     'house_number': '',
        #     'road': '',
        #     'suburb': '',
        #     'city_district': '',
        #     'city': '',
        #     'state': '',
        #     'state_district': ''
        # }

        if parse_address is None:
            print("WARNING: parse_address is None - NOT enriching")
            return

        to_attrs = ['state', 'state_district', 'postcode', 'country']

        label = []
        new_attrs = defaultdict(set)

        #remove some things from the address
        full_address=self.label + ''
        for v, k in parse_address(self.label):
            if k in to_attrs:
                new_attrs[k].add(v)
            else:
                label.append(v)
        self.label = ' '.join(label).upper()

            # print '{} -> {}'.format(full_address, self.label)

        for k, v in new_attrs.iteritems():
            if k == 'country' and len(v):
                country = list(v)[0]
                # Fix for empty label - appears to occur when a singular valid country name is passed and
                # the address library returns an empty label but still populates the country flag on an Address object
                if self.label == '' or self.label is None:
                    self.label = country.upper()
                try:
                    if len(country) == 3:
                        cc = attributes.CountryCode.from_alpha3(country.upper())
                    elif len(country) == 2:
                        cc = country.upper()
                    else:
                        country = attributes.CountryName.best_match(country)
                        cc = pycountry.countries.get(name=country).alpha2
                    self.set_attr('country', cc)
                except:
                    pass
            else:
                for _ in v:
                    if _.strip():
                        self.set_attr(k, _.upper())


class Port(Location):
    """Any type of transit point"""
    pass


class Airport(Port):
    """A port where flights leave from - to be considered an airport object it must appear in [this list](airports.md) otherwise it would be represented as a "Location" """

    attrs = {
        'city': attributes.String,
        'country': attributes.CountryCode,
    }

    def enrich(self):

        if not len(self.label) == 3:
            raise SchemaAttributesInvalidIATA('Invalid IATA Code: {}'.format(self.label))

        try:
            airport = airports.airport_iata(self.label)
        except KeyError, AssertionError:
             raise ValueError('Unknown IATA code : {}'.format(self.label))

        self.iata = self.label

        self.label = '{} ({})'.format(airport.name, airport.iata)

        code=attributes.CountryCode.best_match_from_name(airport.country)

        self.set_attr('country', code)
        self.set_attr('city', airport.city)
        self.set_attr('geoloc', '{},{}'.format(airport.lat, airport.lon))


transactions.Departed.links.append(Location)
transactions.Arrived.links.append(Location)
