# serene_index

Take data on HDFS, convert it to the standardised SCHEMA and index it into SOLR


Logic around update inplace


the LOADED repo has a list of folders representing catalogue IDs (CID)

loaded
 |-----00000001
 |-----00000002
 |....

Each of these folders has n x <FILENAME>.json files representing the data stored on HDFS.

THe contents of each <FILENAME>.json file is a list of SHA256 hashes for the corresponding source files stored
on HDFS in <FILENAME>.

In this manner we can limit our indexing to a particular set of files / documents or reindex the whole thing.

The output of the index job stage is a similarly defined INDEXED repo which has a json file containing a list of all
source file hashes contained in the index.


if the --update-inplace option = FALSE (the default) the following logic is applied:


open the list of hashes from the indexed repo: indexed/<CID>/*.json

This indicates what is already stored in the index.

open the list of hashes from the loaded repo: loaded/<CID>/*.json

start with the list of all files loaded in HDFS

for all hashes found in the indexed repo (ie those files already in the index), blacklist the hashes found in that file
on HDFS until all indexed hashes are processed

for all loaded files where all hashes have been processed, exclude them from being processed

process the remaining files.


if the --update-inplace option = TRUE the following logic applies:

start with a list of all files loaded/<CID>/*.json

sort them alphabetically

start from the oldest (the top of the list) and see if the data appears lower down
blacklist hashes in files that have data higher up
if a file has all hashes blacklisted remove it from processing

## Configuration

This module expects a configuration file to exist at `/etc/serene/conf.ini` with various configuration items.

A blank, sample has been provided [here](config/sample_serene_index.ini).
