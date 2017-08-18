import authkerb
import os
import logging

from twisted.cred.portal import IRealm, Portal
from twisted.web.guard import HTTPAuthSessionWrapper
from twisted.web.resource import IResource
from uuid import uuid4 as mkuuid
from sp_queries import check_params, make_user_filters, get_user
from sp_ldap import LDAPUser

import collections

import datetime
from twisted.web.server import NOT_DONE_YET
from twisted.web import server
from twisted.internet import task
from twisted.web.client import getPage
import sys
from twisted.internet import reactor
from twisted.python import log
from twisted.web import proxy
from twisted.web.resource import Resource, ErrorPage
from twisted.python.compat import urllib_parse
import json
from zope.interface import implements


from remote_log import splunk
import configuration

import urllib
from serene_metadata import DEFINED_FIELDS_DICT

# default encoding for queries and responses
ENCODING = 'utf-8'
DEBUG = False

def setup_logging(level):
    logger = logging.getLogger('abac-proxy')
    logger.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)

    formatter = logging.Formatter('%(levelname)s: %(message)s')
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    return logger


syslog = setup_logging(logging.INFO)

STATS_FIELDS = map(
    lambda _: _.name(),
    filter(
        lambda _: getattr(_, 'PROXY_STATS', False) == True,
        DEFINED_FIELDS_DICT.values()
    )
)

def mk_stats(d, results):

    stats = collections.defaultdict(lambda: collections.defaultdict(int))

    for f in STATS_FIELDS:
        for doc in results:

            if f not in doc:
                continue

            if type(doc[f]) is list:
                for _ in doc[f]:
                    stats[f][_] += 1
            else:

                stats[f][doc[f]] +=1

    for field, counts in stats.iteritems():
        for value, count in counts.iteritems():
            d['{}-{}'.format(field,value)] = count


class ParseResponse(proxy.ProxyClient, Resource):
    """
    Parse the response coming back to the client from the SOLR servers and extract statistics
    """

    def __init__(self, command, rest, version, headers, data, father, user, uuid, resource, request):
        proxy.ProxyClient.__init__(self, command, rest, version, headers, data, father)
        # HTTP11ClientProtocol.__init__(self)

        assert isinstance(user, LDAPUser)
        self.buffer = ''
        self.user = user
        self.uuid = uuid
        self.resource = resource
        self.request = request

    def connectionMade(self):
        syslog.debug('connected!')
        proxy.ProxyClient.connectionMade(self)
        # self.return_error(500, "BLAH")

    def return_error(self, code, message):
        self.resource.error(self.request, code, message)
        proxy.ProxyClient.handleResponseEnd(self)

    def handleHeader(self, key, value):
        syslog.debug('header received {}:{}'.format(key, value))
        proxy.ProxyClient.handleHeader(self, key, value)

    def handleResponseEnd(self):
        """
        Finish the original request, indicating that the response has been
        completely written to it, and disconnect the outgoing transport.
        """
        if self._finished:
            return
        response = json.loads(self.buffer)

        try:
               details = {
                   'qtime' : response['responseHeader']['QTime'],
                   'numfound': response['response']['numFound'],
                   'returned' : len(response['response']['docs'])
               }

               # log.msg(msg)
               mk_stats(details, response['response']['docs'])
               splunk.mklog(user=self.user, action='RESULTS', details='UUID:{} '.format(self.uuid) + ' '.join([u'{}:{}'.format(k.upper(),v) for k,v in details.iteritems()]))

        except KeyError:
               error = response['error']['msg']
               splunk.mklog(user=self.user, action='FAILURE', details='UUID:{} '.format(self.uuid) + u'MSG:{}'.format(error.replace(' ','+')))

        proxy.ProxyClient.handleResponseEnd(self)

    def handleResponsePart(self, buffer):
        self.buffer += buffer
        self.father.write(buffer)


class ParseResponseFactory(proxy.ProxyClientFactory):
    def __init__(self, command, rest, version, headers, data, father, user, uuid, resource, request):
        self.father = father
        self.command = command
        self.rest = rest
        self.headers = headers
        self.data = data
        self.version = version
        self.user = user
        self.uuid = uuid
        self.request = request
        self.resource = resource

    def buildProtocol(self, addr):
        syslog.debug('Build protocol {}'.format(addr))
        return ParseResponse(self.command, self.rest, self.version,
                             self.headers, self.data, self.father, self.user, self.uuid, self.resource, self.request)


sorted_kvs = lambda d: sorted(d, key=lambda k:k[0])

class SereneReverseProxy(Resource):
    isLeaf = True

    host = configuration.SOLR_ENDPOINT
    port = configuration.SOLR_PORT

    def __init__(self, user):

        Resource.__init__(self)
        self.uuid = uuid = mkuuid()

        #First thing we do is get the user object
        try:
            #this turns a username into a LDAPUser object (with attributes)
            self.user = get_user(user)
        except Exception as e:
            splunk.mklog(user=user, action='__ERROR', details='UUID:{} Error getting initial credentials: {}'.format(uuid, e.message))
            self.user = None

    @staticmethod
    def error(request, code, message):
        request.setResponseCode(code)
        request.setHeader(b"content-type", b"text/html; charset={}".format(ENCODING))
        return 'Error: {} {}'.format(code, message)

    def render(self, request):
        """
        Render a request by forwarding it to the proxied server.
        """

        if not self.user:
            return self.error(request, 500, 'Server error')

        host = self.host + u":" + str(self.port)

        request.requestHeaders.setRawHeaders(b"host", [host.encode('ascii')])

        params = urllib_parse.urlparse(request.uri)

        # params.netloc = host
        params = params._asdict()

        if not params['path'].startswith('/solr/{}/'.format(configuration.COLLECTION)):
            splunk.mklog(user=self.user, action='REQUEST', details='DENIED ACCESS TO: {}'.format(params['path']))
            return self.error(request, 404, 'Bad URL')

        params['host'] = host

        query_params = []
        for p in params['query'].split('&'):
            key, value = p.split('=')
            if not value.strip():
                continue
            else:
                query_params.append((key, urllib.unquote(value).decode(ENCODING)))

        splunk.mklog(user=self.user, action='REQUEST', details=u'UUID:{} '.format(self.uuid) + u' '.join(u'{}:{}'.format(k, v.replace(' ','+')) for k,v in sorted_kvs(query_params)))

        try:
            check_params(query_params, user=self.user, uuid=self.uuid)
        except ValueError:
            return self.error(request, 403, 'Bad query params')

        try:
            additional_params = make_user_filters(self.user)
        except Exception as e:
            splunk.mklog(user=self.user, action='__ERROR', details='UUID:{} Error making user filters: {}'.format(self.uuid, e.message))
            return self.error(request, 500, 'Server error')

        splunk.mklog(user=self.user, action='uFILTER', details='UUID:{} '.format(self.uuid) + ' '.join('{}:{}'.format(_[0],_[1]) for _ in sorted_kvs(additional_params)))

        timeout_params = [
            ('timeAllowed', '30000')  #Maximum query time in MS
        ]

        query = urllib.urlencode([(_[0], _[1].encode(ENCODING),) for _ in query_params + additional_params + timeout_params])

        rest = 'http://{}/solr/{}/select?{}'.format(host, configuration.COLLECTION, query)
        clientFactory = ParseResponseFactory(
            command =request.method,
            rest = rest,
            version = request.clientproto,
            headers = {}, #request.getAllHeaders(),
            data = '',
            father = request,
            user = self.user,
            uuid=self.uuid,
            resource = self,
            request = request
        )

        reactor.connectTCP(self.host, self.port, clientFactory)
        return NOT_DONE_YET


class ADSecureRealm(object):
    implements(IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if IResource in interfaces:
            return (IResource, SereneReverseProxy(avatarId), lambda: None)


os.environ['KRB5_KTNAME'] = configuration.KEYTAB_LOCATION
negotiateChecker = authkerb.NegotiateCredentialsChecker()

portal = Portal(ADSecureRealm(), [negotiateChecker])

negotiateFactory = authkerb.NegotiateCredentialFactory('HTTP')

resource = HTTPAuthSessionWrapper(portal, [negotiateFactory])
site = server.Site(resource)


def report_error(value):
    now = datetime.datetime.now().isoformat()
    splunk.rawlog(details=u'{} {}-SOLR ERROR {}'.format(now, configuration.SYSTEM_NAME, value))


def parse_clusterstate(value):

    try:
        result = json.loads(value)
        now = datetime.datetime.now().isoformat()
        nodes = len(result['cluster']['live_nodes'])
        shards = result['cluster']['collections'][configuration.COLLECTION]['shards']
        active_shards = filter(lambda _:_['state'] == 'active', shards.itervalues())
        details = u'{} {}-SOLR OKAY live_nodes={} shards={} active_shards={}'.format(
            now,
            configuration.SYSTEM_NAME,
            nodes,
            len(shards),
            len(active_shards)
        )
        splunk.rawlog(details)

    except Exception as e:
        report_error(e.message)


def check_system_health():

    host = configuration.SOLR_ENDPOINT
    port = configuration.SOLR_PORT

    endpoint = 'http://{}:{}/solr/admin/collections?action=CLUSTERSTATUS&wt=json'.format(host, port)

    getPage(endpoint).addCallbacks(callback=parse_clusterstate, errback=report_error)


def main():
    log.startLogging(sys.stdout)
    from twisted.internet import endpoints, reactor
    splunk.setup(reactor)
    splunk.mklog(user=None, action='SYSTEM', details='STARTUP')

    def shutdown(reason, reactor, stopping=[]):

        if stopping: return

        stopping.append(True)
        if reason:
            log.msg(reason.value)

        reactor.callWhenRunning(reactor.stop)

    endpoint = endpoints.serverFromString(reactor, configuration.PROXY_ENDPOINT)

    d = endpoint.listen(site)
    d.addErrback(shutdown, reactor)

    #check system health regularly
    task.LoopingCall(check_system_health).start(60, now=True)
    reactor.run()


if __name__ == '__main__':
    main()
else:
    from twisted.application import service, strports
    application = service.Application("proxy_modify_requests")
    strports.service(configuration.PROXY_ENDPOINT, site).setServiceParent(application)
