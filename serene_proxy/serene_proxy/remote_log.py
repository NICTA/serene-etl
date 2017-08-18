from twisted.internet.protocol import Protocol, ReconnectingClientFactory
import datetime
from configuration import LOGGING_ENDPOINTS, SYSTEM_NAME


class RemoteLoggerFactory(ReconnectingClientFactory):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connected = False
        self.queue = []

    def startedConnecting(self, connector):
        print 'Starting connection'

    def buildProtocol(self, addr):
        print 'Connected: {}'.format(addr)
        self.connected = True
        self.logger = Protocol()
        return self.logger

    def clientConnectionLost(self, connector, unused_reason):
        print 'Lost connection.'
        self.connected = False
        ReconnectingClientFactory.clientConnectionLost(self, connector, unused_reason)

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed.'
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def log(self, message):
        if self.connected:
            self.logger.transport.write(message.encode('utf-8') + '\n')

            if self.queue:
                for q in self.queue:
                    self.logger.transport.write(q.encode('utf-8') +'\n')
            self.queue = []
        else:
            self.queue.append(message)

    def mklog(self, user, action, details):
        log = u'{} {}-PROXY {} {} {}'.format(SYSTEM_NAME, datetime.datetime.now().isoformat(), user, action, details.replace('\n','+'))
        self.log(log)


class RemoteLoggers(object):
    """
    Support multiple remote logging TCP endpoints
    """

    def __init__(self, endpoints):
        self.endpoints = endpoints
        self.loggers = []

        for ep in endpoints:
            self.loggers.append(RemoteLoggerFactory(host=ep[0], port=ep[1]))

    def setup(self, reactor):

        for logger in self.loggers:
            reactor.connectTCP(logger.host, logger.port, logger)

    def mklog(self, user, action, details):

        for logger in self.loggers:
            logger.mklog(user, action, details)

    def rawlog(self, details):
        for logger in self.loggers:
            logger.log(details)

splunk = RemoteLoggers(LOGGING_ENDPOINTS)
