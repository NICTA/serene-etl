#!/bin/bash

patch -R $1/managed-schema < $1/managed-schema.patch
patch -R $1/solrconfig.xml < $1/solrconfig.patch
mv $1/managed-schema $1/schema.xml
rm $1/*.patch
tar -zcvf solr_config.tgz $1
rm apply_patch.sh
