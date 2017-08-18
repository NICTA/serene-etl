import json
import collections
from itertools import chain

try:
    from pyspark.sql import SQLContext, Row
    from pyspark.sql.functions import collect_list, collect_set, create_map, column, lit
except ImportError:
    pass


def to_str(_):
    if isinstance(_, basestring):
        return _
    return json.dumps(_, encoding='utf-8')


def remove_none(_):
    return {k: v for k, v in _.iteritems() if v}

class TableJoinHelper(object):

    @classmethod
    def make_tables(cls, rdd, table_maps, table_renames=None, describe=True, sqlContext=None):
        """

        rdd: the source rdd that contains all tables

        Table maps is a dictionary of name:lambda functions where the name is the table name, the lambda function is the
        fitler applied (to rdd) that will extract that specific table from the rdd and then load it to a dataframe

        table_renames is a dictionary of name:[(src,dest), (src,dest)] renames for columns as required (or none)

        describe is a bool indicating if the dataset should be describe()d after loading

        """

        self = cls()

        if sqlContext is None:
            self.sqlContext = sqlContext = SQLContext(rdd.ctx)
        else:
            self.sqlContext = sqlContext

        self.tables = {}

        rdd = rdd.cache()

        all_rdds = [rdd]

        print 'Loading from RDD with {:,} records'.format(rdd.count())

        for name, lf in table_maps.iteritems():

            used = rdd.filter(lf)
            self.tables[name] = sqlContext.read.json(used.map(to_str)).cache()

            # We want to keep records that have not been converted to a table...
            rdd = rdd.filter(lambda _: not lf(_)).cache()
            all_rdds.append(rdd)

            if describe:
                print 'DESCRIBE TABLE "{}" - {:,} records'.format(name, self.tables[name].count())
                for c in self.tables[name].columns:
                    print c
                print '---'

            if table_renames and name in table_renames:
                for (src, dest) in table_renames[name]:
                    new_table = self.tables[name].withColumnRenamed(src, dest).cache()
                    self.tables[name].unpersist()
                    self.tables[name] = new_table

        self.unused_records = rdd.coalesce(rdd.getNumPartitions()).cache()
        ur_count = self.unused_records.count()
        if ur_count:
            print 'WARNING: {:,} records remain in rdd'.format(ur_count)

        for old_rdd in all_rdds:
            old_rdd.unpersist()

        return self

    @classmethod
    def from_tables(cls, tables):
        self = cls()
        self.tables = tables
        return self

    def overlap(self, keyname):
        """
        Determine the intersection in keys (count) tables that have column "keyname"
        """

        all_df = []

        for name, _df in self.tables.iteritems():

            if keyname not in _df.columns:
                print 'Skipping "{}" because it does not have a column called "{}"'.format(name, keyname)
                continue

            def m(_):
                return _.asDict()[keyname], name

            rdd = _df.select(keyname).rdd
            all_df.append(rdd.map(m).coalesce(rdd.getNumPartitions()))

        first = all_df[0]

        for _df in all_df[1:]:
            first = first.union(_df)

        for table_names, count in first.groupByKey().map(lambda _: tuple(sorted(set(_[1])))).countByValue().iteritems():

            print '{:,} of the keys in column {} appear in all of {}'.format(count, keyname, table_names)
            for tn in table_names:
                t_count = self.tables[tn].count()
                print 'That is {:.0%} of {}'.format(float(count)/t_count, tn)
            print '--'

    def check_max_keys(self, keyname):
        """
        Determine if this RDD's keys look to be "unbalanced" - ie a key which has a large number of records
        """

        for name, _df in self.tables.iteritems():

            if keyname not in _df.columns:
                print 'Skipping "{}" because it does not have a column called "{}"'.format(name, keyname)
                continue

            sorted_count = _df.groupBy(keyname).count().sort('count', ascending=False).first()
            print '"{}" heaviest key is "{}" with {:,} records'.format(name, sorted_count[keyname], sorted_count['count'])

    def get_map(self, tablename):
        return create_map(list(chain(*((lit(name), column(name)) for name in self.tables[tablename].columns)))).alias('{}_records'.format(tablename))

    def key_by(self, keyname, tablename):
        """
        transform the `keyname` column to TABLENAME_key and nest the record into TABLENAME_records column as a map
        """

        table = self.tables[tablename]
        key_col = '{}_key'.format(tablename)
        records = self.get_map(tablename)

        return table.select(column(keyname).alias(key_col), records).cache()

    def collapse_record_by_key(self, keyname, tablename):
        """
        Collapse a record by column `keyname`
        key is transformed to TABLENAME_key
        record is a transformed into list of maps (one for each record)
        """

        table = self.tables[tablename]
        key_col = '{}_key'.format(tablename)
        records = self.get_map(tablename)

        # Can't figure out a better way to do this - ie keep each record together - other than converting to JSON...

        return table.select(column(keyname).alias(key_col), records).groupBy(key_col).agg(collect_list).cache()

    def collapse_by_key(self, keyname, tablename):
        """
        Similar to collapse record by key except column names remain and are collapsed as a set
       """

        table = self.tables[tablename]
        key_col = column(keyname).alias('{}_key'.format(tablename))

        agg_func = [collect_set(_).alias(_) for _ in table.columns]

        return table.groupBy(key_col).agg(*agg_func).cache()

    def join_by_key(self, tables_map):

        names = tables_map.keys()
        base_name = names[0]
        base_tbl = tables_map[base_name]
        keys = ['{}_key'.format(base_name)]

        for name in names[1:]:
            base_tbl = base_tbl.join(tables_map[name], on=base_tbl['{}_key'.format(base_name)] == tables_map[name]['{}_key'.format(name)], how='outer')
            keys.append('{}_key'.format(name))

        all_keys = base_tbl
        not_all_keys = base_tbl.filter("False")

        for _ in keys:
            _all_keys = all_keys.filter(all_keys[_].isNotNull())
            not_all_keys = not_all_keys.union(all_keys.filter(all_keys[_].isNull()))
            all_keys = _all_keys

        return not_all_keys, all_keys
