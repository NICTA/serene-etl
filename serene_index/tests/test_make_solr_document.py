from unittest import TestCase
import importlib
import ast
import json
import logging


from ConfigParser import ConfigParser
from io import StringIO
from mock import patch

#ignore pycountry debug logging
quiet = logging.getLogger('pycountry.db')
quiet.setLevel(logging.ERROR)


class TestMake_solr_document(TestCase):

    record = {
        "src_file_rec": "travel/travel.csv:1",
        "dob": "17/04/1979",
        "name": "George Jetson",
        "passport_no": "99999999",
        "passport_country": "NZ",
        "departure_port": "SYD",
        "arrival_port": "AKL"
    }

    meta = {
        "src_file_cid": 10
    }

    result = {
        'Airport.country_ss': [u'NZ', u'AU'],
        'Airport.geoloc': [u'-37.008056,174.791667', u'-33.946111,151.177222'],
        'Airport_ss': [u'Sydney Intl (SYD)', u'Auckland Intl (AKL)'],
        'Departed.timestamp_ss': [u'2013-12-10T00:00:00Z'],
        'Entity_ss': [u'GEORGE JETSON'],
        'Event_ss': [u'UNKNOWN'],
        'Flight_ss': [u'UNKNOWN'],
        'IssuedDocument.country_ss': [u'NZ'],
        'IssuedDocument_ss': [u'99999999'],
        'Location.geoloc': [u'-37.008056,174.791667', u'-33.946111,151.177222'],
        'Location_ss': [u'Sydney Intl (SYD)', u'Auckland Intl (AKL)'],
        'Passport.country_ss': [u'NZ'],
        'Passport_ss': [u'99999999'],
        'Person_ss': [u'GEORGE JETSON'],
        'Port.geoloc': [u'-37.008056,174.791667', u'-33.946111,151.177222'],
        'Port_ss': [u'Sydney Intl (SYD)', u'Auckland Intl (AKL)'],
        'Travelled.timestamp_ss': [u'2013-12-10T00:00:00Z'],
        'arrival_port_ss': [u'AKL'],
        'attr_types': [u'Airport.geoloc', u'Departed.timestamp', u'Airport.country', u'city',  u'dob', u'country',
                       u'IssuedDocument.country', u'Location.geoloc', u'arrival_port', u'departure_port', u'geoloc',
                       u'Travelled.timestamp', u'timestamp', u'Passport.country',u'Port.geoloc'],
        'city_ss': [u'Sydney', u'Auckland'],
        'country_ss': [u'NZ', u'AU'],
        'data': u'["Person","GEORGE JETSON",[["dob","1979-04-17T00:00:00Z"]],[["Holds",[],[["Passport","99999999",'
                '[["country","NZ"]],[["Travelled",[["timestamp","2013-12-10T00:00:00Z"]],[["Flight","UNKNOWN",'
                '[["departure_port","SYD"],["arrival_port","AKL"]],[["Departed",[["timestamp",'
                '"2013-12-10T00:00:00Z"]],[["Airport","Sydney Intl (SYD)",[["country","AU"],'
                '["geoloc","-33.946111,151.177222"],["city","Sydney"]],[]]]],["Arrived",[],[["Airport",'
                '"Auckland Intl (AKL)",[["country","NZ"],["geoloc","-37.008056,174.791667"],["city","Auckland"]],'
                '[]]]]]]]]]]]]]]',
        'departure_port_ss': [u'SYD'],
        'dob_dts': [u'1979-04-17T00:00:00Z'],
        'geoloc': [u'-37.008056,174.791667', u'-33.946111,151.177222'],
        'id': u'6daf5bc24d75fe36d25700633359fbe7c166d66ef19fc8eba236fa8670e7fa40',
        'link_types': [u'Travelled', u'Holds', u'Arrived', u'Departed'],
        'object_types': [u'Flight', u'Entity', u'Person', u'Airport', u'Location', u'Passport', u'IssuedDocument',
                         u'Port', u'Event'],
        'raw': u'{"arrival_port":"AKL","departure_port":"SYD","dob":"17/04/1979","name":"George Jetson",' +
               '"passport_country":"NZ","passport_no":"99999999"}',
        'src_file_cid': 10,
        'src_file_rec': [u'test/file_1:1'],
        'timestamp_ss': [u'2013-12-10T00:00:00Z']
    }

    @patch('serene_metadata.config.SereneConfig')
    def setUp(self, mock_config):

        from serene_index.helpers.index_helpers import mk_error_counter, make_solr_document
        from serene_metadata import generate_example_metadata

        self.error_counter = mk_error_counter()

        module = importlib.import_module('serene_index.modules.module_flight')
        self.builder = getattr(module, 'record_builder', None)
        generated_metadata = generate_example_metadata()
        print json.dumps(generated_metadata, indent=1)

        self.meta.update(generated_metadata)
        self.result.update(generated_metadata)

        self.solr_doc = make_solr_document(r=self.record, builder=self.builder, base=self.meta, debug=False, error_counter=self.error_counter)

    def tearDown(self):
        self.error_counter = None

    def test_make_solr_document(self):
        self.maxDiff = None
        self.assertDictEqual(self.result, self.solr_doc)
        # a = json.dumps(self.solr_doc, indent=1, sort_keys=True)
        # b = json.dumps(self.result, indent=1, sort_keys=True)

    def test_json_correct(self):
        rec = json.dumps(self.solr_doc)
        self.assertTrue(json.loads(rec), 'Solr document does not parse as json')
