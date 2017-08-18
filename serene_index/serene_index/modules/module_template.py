from serene_schema import entities


def dataset_loader(input_path, sc, args):

    return None

dataset_loader = None


def data_preprocess(rdd):
    """
    This function receives a RDD: sc.textFile(input_path).map(lambda _:json.loads(_))
    """

    return rdd


def record_builder(record, error_counter, metadata):
    """
        Example record builder. Receives a dictionary and should return a serene schema object

        Additional fields are error_counter which is shown at the end of a job and
        metadata which shows any metadata related to the record

    """

    #create the object based on the input record
    try:
        person = entities.Person.parts_unknown(record['name'])
    except KeyError:
        # If we don't have name in the record
        person = entities.Entity('UNKNOWN')
        error_counter.add('No name on person')

    return person
