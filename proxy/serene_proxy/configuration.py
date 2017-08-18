import platform

PROXY_ENDPOINT = 'tcp:8123:interface=localhost'
PROXY_ENDPOINT = 'tcp:8123'
KEYTAB_LOCATION = '/etc/krb5.keytab'
SOLR_PORT = 8983
COLLECTION = 'serene'
SYSTEM_NAME = COLLECTION.upper()

LOGGING_ENDPOINTS = [
    ('cdhmgt02', 514)
]

SOLR_ENDPOINT = 'cdhsvr01'

DOMAIN ='DOMAIN.LOCAL'
DOMAIN_CONTOLLER = 'domaincontroller01' + '.' + DOMAIN

LDAP_QUERY_USER = 'CN=jenkins,CN=Managed Service Accounts,DC=domain,DC=local'
LDAP_QUERY_PASS = '<INSERT YOUR PASSWORD HERE>'
LDAP_USER_SEARCH_BASE = 'DC=domain,DC=local'

#dont filter by AD group
LDAP_USER_FILTER = '(&(CN={}))'

#filter by AD group using LDAP_MATCHING_RULE_IN_CHAIN
# LDAP_USER_FILTER = '(&(CN={})(memberof:1.2.840.113556.1.4.1941:=CN=GROUPNAME,OU=DIRECTORY,OU=DIRECTORY,DC=LOCAL,DC=DOMAIN))'

# Multi valued attributes from AD

# Multi valued
permission_multi_maps = {
    #field ABAC in serene_metadata.fields: adPropertyName
}

# Single valued
permission_single_maps = {
    'department': 'department',
}

#additional user details sent to the logging endpoint
ADDITIONAL_USER_NAME_PARTS = [
    'department'
]

