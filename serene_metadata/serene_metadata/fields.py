
from abac import *


class SereneMetaField(object):
    # Can this field have multiple values on a single record / document ?
    MULTIVALUED = False

    #Should the proxy generate stats for each value it sees for this field?
    PROXY_STATS = False

    #SOLR Type
    TYPE = 'string'

    # Does the serene_index runner require this field during indexing?
    REQUIRED_AT_INDEX = True

    # Does the serene_load runner require this field during loading to HDFS?
    REQUIRED_AT_LOAD = False

    @classmethod
    def name(self):
        return self.__name__.lower()

    @classmethod
    def validate_final(cls, value):
        """
        Validate that a value is suitable based on TYPE and MULTIVALUED
        """

        if type(value) is list:
            if len(value) > 1:
                assert cls.MULTIVALUED is True, 'List for a non-multivalued field'

        else:
            value = [value]

        for _ in value:

            assert _ is not None, \
                u'{} received an empty value "{}"'.format(cls, value)

            if cls.TYPE == 'string':
                assert isinstance(_, basestring), \
                    u'{} requires type=string but received something else "{}"'.format(cls, value)

                assert _
            elif cls.TYPE == 'int':
                assert isinstance(_, int), \
                    u'{} requires type=int but received something else "{}"'.format(cls, value)

        if cls.MULTIVALUED is False:
            return value[0]
        else:
            return value


    MAP_FROM_CATALOGUE = None

    @classmethod
    def catalogue_map(cls, entry):
        """
        This function is called from serene_index to add metadata from your data catalogue repo (see serene_index)
        into the specified SereneMetaField typically joined on the data's "catalogue id"

        See examples below
        """

        raise NotImplementedError()

    @classmethod
    def example(cls):
        raise NotImplementedError()






class src_file_rec(SereneMetaField):
    """
    Source file record: this field is designed to be able to answer the question "where did this data come from exactly"

    It could be a:
    * UUID
    * pathname/filename/row tuple (as a string)
    * anything else your organisation uses to uniquely identify data at a record level

    It is multi-valued because for some (many) records the source might be multiple peices of data (for example, where you
    have joined two tables together...)

    """
    MULTIVALUED = True
    REQUIRED_AT_LOAD = True
    #The field used in the load step as the primary identifier? Only one field can have PRIMARY_ID = Truegj
    PRIMARY_ID = True

    @classmethod
    def example(cls):
        return [u'10/test_data.csv:10']

class src_file_cid(SereneMetaField):
    """
    Source file Catalog ID: this field should allow lookup of more information about the source dataset to answer
    the question "where did this data come from generally"

    Change to MULTIVALUED = True if you're joining data from multiple source datasets (otherwise you can only have one cid)
    """
    TYPE = 'int'
    MULTIVALUED = False
    CATALOGUE_ID = True
    PROXY_STATS = True

    @classmethod
    def example(cls):
        return 10


class CatalogueMapMax32Upper(object):

    @classmethod
    def catalogue_map(cls, entry):
        assert len(entry) < 32, 'Max 32 characters'
        return entry.upper().strip()



class src_file_src(CatalogueMapMax32Upper, SereneMetaField):
    """
    Data source or owner - ie external provider
    """

    MAP_FROM_CATALOGUE = 'Owner (External)'

    @classmethod
    def example(cls):
        return u'Department'

