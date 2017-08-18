"""

Events - things that have a timestamp

"""
import base, attributes, transactions


class Event(base.SchemaBase):
    """ Event base type - all events must have at the very least a timestamp (date and time) in UTC timezone"""
    attrs = {
        'timestamp': attributes.Datetimestamp
    }


class MultiDayEvent(base.SchemaBase):
    """Similar to Event but for events that occur over multiple days"""
    attrs = {
        'start_dt': attributes.Datestamp,
        'end_dt':attributes.Datestamp
    }


class Flight(Event):
    """
    A flight from one port to another - label is the flight number
    attributes route show the other airports visited

    """
    links = Event.links + [
        transactions.Arrived,
        transactions.Departed
    ]

    attrs = {
        'route': attributes.String,
        'departure_time': attributes.Datetimestamp,
        'departure_port': attributes.AirportIATA,
        'arrival_time': attributes.Datetimestamp,
        'arrival_port': attributes.AirportIATA
    }

transactions.Travelled.links.append(Flight)

