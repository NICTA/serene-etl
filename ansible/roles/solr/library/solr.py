#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import defaultdict
import json
import requests
from ansible.module_utils.basic import *
import platform
hostname = platform.node().split('.')[0]
import re

action = 'http://localhost:8983/solr/admin/collections?action=ADDREPLICA&collection={}&node={}_solr&shard=shard{}'
# arguments that the module gets in various actions
MODULE_ARGUMENTS = ['hosts', 'target_rack', 'group', 'collection']


HOST_PATERN = r'([a-zA-Z]+)([\d]+)'

def main():

    module = AnsibleModule(argument_spec=dict((argument, {'type': 'str'}) for argument in MODULE_ARGUMENTS))
    group = module.params['group']
    collection = module.params['collection']
    target_rack = int(module.params['target_rack'])


    #yes this is a _very_ hacky way of doing this - turning a python printed dictionary into valid JSON...
    hosts = module.params['hosts'].strip()\
        .replace("'",'"')\
        .replace('True','true')\
        .replace('False','false')\
        .replace('None','null')\
        .replace(': u"',': "')\
        .replace('u"',' "')

    try:
        host_data = json.loads(hosts)
    except ValueError:
        print hosts
        raise

    num_shards = host_data['num_shards']
    layout = host_data['layout']
    all_hosts = host_data['groups'][group]
    ports = []

    for _ in layout:
        ports.extend(_['ports'])

    host_rack = {}

    for host in all_hosts:
        assert host in host_data
        assert 'host_rack' in host_data[host], json.dumps(host_data[host])
        host_rack[host] = int(host_data[host]['host_rack']['stdout'])

    target_hosts = [_[0] for _ in filter(lambda _:_[1] == target_rack, host_rack.iteritems())]

    cores = []

    for host in target_hosts:
        for port in ports:
            cores.append('{}:{}'.format(host, port))

    assert len(cores) == num_shards

    shards = []

    print hostname
    for shard, core in enumerate(sorted(cores)):

        print core

        if core.startswith(hostname):
            #solr shards start at number 1!
            shards.append(action.format(collection, core, shard+1))

    assert shards

    for shard in shards:

        response = requests.get(shard)
        assert int(response.status_code) == 200, 'Failed on {}'.format(shard)


    return module.exit_json(msg='Done')


main()
