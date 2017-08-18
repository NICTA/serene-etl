# serene_load

This repo is the first step in getting data into Solr

It contains a number of modules which all

1. Read data from the filesystem (actually a remote share...)
2. Convert the data to the appropriate format -> JSON
3. Write the data to HDFS

It runs on a single machine but is multi-threaded.

Available settings for arguments variable:

| option | example |
| --- | --- |
| enc | "enc":"utf-8" |
| sep | "sep":"," |
| header_sep | "header_sep":"," |
| lineend | "lineend":"\n" |

### Output

The output of a load job is one or more files on HDFS in compressed (bz2 because it's splittable and natively supported)
json format where each line is a single "dictionary" record containing key-value pairs from the source data.

For example, the following csv (let's say it was called "inventory.csv"):

| column_a | column_b | column_c |
| --- | --- | --- |
| pen | red | 4291 |
| pencil | graphite | 392 |
| pen | blue | 100 |

 would be converted to the following json

 ```json
 {"column_a": "pen", "column_b": "red", "column_c": 4291, "src_file_file": "inventory.csv", "src_file_row": 1}
 {"column_a": "pencil", "column_b": "graphite", "column_c": 392, "src_file_file": "inventory.csv", "src_file_row": 2}
 {"column_a": "pen", "column_b": "blue", "column_c": 100, "src_file_file": "inventory.csv", "src_file_row": 3}
 ```

There's no guarantees on the ordering of the output json (and actually we don't care because we add source file and row to the output).

We'd like to make best use of HDFS storage though so we definitely don't want many small json files - we'd ideally have
a few (eg 20) large json.bz2 files which we know are splittable

Also, because we can't write to the one output file at the same time, the number of output files is determined in part
by the number of output writers

Where there are many input files that are homogeneous (the same) then we try to have N output files that are going
to contain many input files (where N is the number of workers)

Where we have a small number of large input files that are heterogeneous (different) we can also have <=N output files
by giving each worker multiple files to process

| Input file count | Input size | Homogeneous (the same) | Number of output files |
| --- | --- | --- | --- |
| > number of workers | Large | Yes | = number of workers |
| > number of workers | Small | Yes | = number of workers |
| > number of workers | Large | No | = number of workers |
| > number of workers | Small | No | = number of workers |
| < number of workers | Large | Yes | = number of files |
| < number of workers | Small | Yes | = number of files |
| < number of workers | Large | No | = number of files |
| < number of workers | Small | No | = number of files |

From the above table, you can see that we need to adjust the number of workers so that no output file is below a certain size

To do this we run a few stages

Stage 1 - scan input path for all files matching the regular expression provided
Stage 2 - determine the file format (eg compressed, zip, etc) and file size
Stage 3 - bundle the files into work bundles so that each worker receives enough files to make a large output