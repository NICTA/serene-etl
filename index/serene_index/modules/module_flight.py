from serene_schema import entities, documents, transactions, locations, events
import datetime
import pytz


def get_birth_date(_):
    d = datetime.datetime.strptime(_, "%d/%m/%Y")
    return datetime.datetime(
        year=int(d.year),
        month=int(d.month),
        day=int(d.day),
        hour=0,
        minute=0,
        second=0,
        tzinfo=pytz.UTC
    )


def record_builder(record, error_counter, metadata):
    person_attrs = {
        'dob': get_birth_date(record['dob'])
    }

    person = entities.Person.parts_unknown(label=record['name'], attrs=person_attrs)

    passport_attrs = {
        'country': record['passport_country']
    }

    passport_no = record['passport_no']
    passport = documents.Passport(passport_no, passport_attrs)

    person.add_link(
        transactions.Holds([
            passport
        ])
    )

    flight_origin = locations.Airport(record['departure_port'])
    flight_destination = locations.Airport(record['arrival_port'])

    flight = events.Flight('UNKNOWN')
    flight.set_attr('departure_port', flight_origin.iata)
    flight.set_attr('arrival_port', flight_destination.iata)
    flight.add_links([
        transactions.Departed([flight_origin], attrs={'timestamp': '2013-12-10T00:00:00Z'}),
        transactions.Arrived([flight_destination])
    ])

    passport.add_link(
        transactions.Travelled([flight], attrs={'timestamp': '2013-12-10T00:00:00Z'})
    )

    return person



