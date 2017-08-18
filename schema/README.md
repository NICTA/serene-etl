# Serene Schema

This repo forms the backbone of the Serene system and provides the following:

* A (Pythonic) way to define the "Ontology" used by Serene
* Some helpers that generate user facing documentation about the Ontology
* A (example) SOLR Config (and data mapper) that will store data in SOLR for indexing, discover and reuse

# Ontology

The Serene Schema provides a Pythonic way to manage the system Ontology. This includes:

* A heirarchical ontological structure with attribute/property and edge/transaction inheritence
* Methods to validate data being mapped to the objects/attributes in the Ontology

#### Updating solr schema

```bash
#!/bin/bash

#example code for modifying the SOLR schema

ZKC="/opt/solr-6.0.0/server/scripts/cloud-scripts/zkcli.sh"
ZKSERVER="manager02"
COLLECTION="serene"

bash $ZKC -z $ZKSERVER -cmd upconfig -n $COLLECTION -d ./solr_config/
curl http://$ZKSERVER:8983/solr/admin/collections?action=RELOAD&name=$COLLECTION
bash $ZKC -z $ZKSERVER -cmd upconfig -n $COLLECTION -d ./solr_config/
bash $ZKC -z $ZKSERVER -cmd linkconfig -c $COLLECTION -n $COLLECTION
bash $ZKC -z $ZKSERVER -cmd get /configs/$COLLECTION/schema.xml | less

# restart solr to reload the schema
```
