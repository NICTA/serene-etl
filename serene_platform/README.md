# serene_platform

This package is the parent package of all `serene` packages.

## Subpackages

Installing this package provides you with the following packages:

* serene_schema
* serene_index
* serene_load
* serene_proxy

## Commands

The packages above provide all the commands required to run any of the serene commands, including the following:

* serene_index
* serene_scan
* serene_load
* serene_proxy

## versioning

The [requirements.txt](requirements.txt) file should always contain all the serene packages, and a specific version to use.

When deploying the serene platform, install this package, which will install all the subpackages.

## Configuration

This module has a sample configuration file, which should be deployed to `/etc/serene/conf.ini`.

It can be found [here](config/sample_serene_index.ini). For documentation on using it, check the [README](config/README.md).

