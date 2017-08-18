# Serene Metadata

This repo helps manage metadata in Serene. It provides the "single source of truth" for how data is tracked and managed.

# Field definitions

Fields are subclassed from serene_metadata.fields

# Hooks

The following hooks can be implemented


## During loading to HDFS

* Do something

## During indexing to SOLR

* ApplyCatalogueMarkings - take markings from your data catalogue and apply them to every record


## During Access via Proxy

* ApplyABAC - build abac rules from fields




