#!/bin/bash -x
# Used as a helper to update the SCHEMA.md output and commit the changes to git

python serene_schema/helpers/markdown.py > doco/SCHEMA.md
