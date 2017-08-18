from nose.tools import *

import datetime
import json
import pytz


from serene_schema import attributes, accounts, locations, events, entities, transactions, schema_exceptions
from serene_schema.repr_to_solr import repr_to_solr, make_json


def print_record(_):
    repr_to_solr(_.repr())
    print json.dumps(json.loads(make_json(repr_to_solr(_.repr()))), sort_keys=True, indent=1)


def test_phone_numbers():
    # create a phone number
    phone = accounts.ITUE164('AU:0291234567')

    # Timestamp for when it was associated
    ts = datetime.datetime.now(tz=attributes.utc)

    person = entities.Person.parts_unknown(label='test PERSON')

    person.set_attr(
        'dob',
        datetime.datetime(year=2010, month=10, day=21, hour=0, minute=0, second=0, tzinfo=pytz.UTC)
    )

    person.add_link(transactions.AssociatedWith([phone], attrs={'timestamp':ts}))

    # Country names come in all formats
    matched = attributes.CountryName.best_match('Australian')
    country = locations.Country(matched)

    # link phone number 1 to a country
    person.add_link(transactions.Located([country]))

    # Generate a solr representation
    print_record(person)


@raises(schema_exceptions.SchemaAttributesInvalidPhoneNumber)
def test_failure_itue():
    accounts.ITUE164('1234')


def test_flight():

    departure_port = locations.Airport('SYD')
    arrival_port = locations.Airport('MEL')

    route = 'SYDMEL'

    flight = events.Flight('QF0000', attrs={
        'route': route,
        'departure_time': datetime.datetime.now(tz=attributes.utc),
        'arrival_time': datetime.datetime.now(tz=attributes.utc),
        'departure_port': 'SYD',
        'arrival_port': 'MEL'
    })

    flight.add_links([
        transactions.Departed([departure_port], attrs={'timestamp': datetime.datetime.now(tz=attributes.utc)}),
        transactions.Arrived([arrival_port])
    ])

    print_record(flight)


@raises(schema_exceptions.SchemaBaseError)
def test_person_fail():
    person = entities.Person('blah BLAH')


def test_person_varieties():
    person = entities.Person.parts_known(givennames='namey MCNAMA', surname=None)
    person2 = entities.Person.parts_known(givennames='namey MCNAM', surname='FACE    face')
    person3 = entities.Person.parts_known(givennames=None, surname='FACE')
    person4 = entities.Person.parts_unknown(label='BLAH mc blah BLAH')
    person.add_link(transactions.AssociatedWith([person2]))
    person.add_link(transactions.AssociatedWith([person3]))
    person.add_link(transactions.AssociatedWith([person4]))

    print_record(person)


@raises(schema_exceptions.SchemaAttributesInvalidEmailAddress)
def test_invalid_email_numbers():
    email = accounts.Email("1234")


@raises(schema_exceptions.SchemaAttributesInvalidEmailAddress)
def test_invalid_email_string():
    email = accounts.Email("cat")


@raises(schema_exceptions.SchemaAttributesInvalidEmailAddress)
def test_invalid_email_double_at():
    email = accounts.Email("1234@domain.com@really")


def test_valid_email():
    email = accounts.Email("bart.simpson@provider.com")


@raises(AssertionError)
def test_person_failure_again():
    entities.Person(('blah', 'BLAH', 'blah BLAH'))

