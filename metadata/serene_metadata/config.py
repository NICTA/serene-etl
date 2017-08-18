from ConfigParser import ConfigParser
import os

class SereneConfig(object):

    CONFIGURATION_PATH = '/etc/serene/conf.ini'

    def __init__(self):
        assert os.path.exists(self.CONFIGURATION_PATH), "could not load configuration from {}".format(self.CONFIGURATION_PATH)
        config = ConfigParser()
        config.read(self.CONFIGURATION_PATH)
        self.config = config

    def get(self, key):
        return self.config.get(self.SECTION_NAME, key)

