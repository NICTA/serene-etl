# serene-proxy

Simple(ish) implementation of a reverse-proxy server using Python Twisted that:

Typically you would put this proxy in a DMZ between your SOLR cluster and your user facing network.

* requires Kerberos Negotiate authentication for all requests coming in
* sends a log of the request to a nominated logging server
* takes the user for that Kerberos request and gets their attribtues from an Active Directory server
* applies filters based on their attributes
* checks the parameters they have supplied
* passes on their request to SOLR
* parses the response received from SOLR and sends statistics about it to a nominated logging server

This results in transparent SSO ABAC for the user.

