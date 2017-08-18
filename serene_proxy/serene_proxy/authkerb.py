import kerberos

from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.credentials import ICredentials
from twisted.cred.error import LoginFailed, UnauthorizedLogin
from twisted.internet import defer
from twisted.internet.threads import deferToThread
from twisted.python import log
from twisted.web.iweb import ICredentialFactory
from zope.interface import implements

class INegotiateCredentials(ICredentials):
    pass


class NegotiateCredentials(object):
    implements(INegotiateCredentials)

    def __init__(self, principal):
        self.principal = principal

class ServerGSSContext(object):
    def __init__(self, serviceType=''):
        self.serviceType = serviceType
        self.context = None

    def __enter__(self):
        try:
            res, self.context = kerberos.authGSSServerInit(self.serviceType)
        except kerberos.KrbError as e:
            msg = repr(e)
            log.msg(msg)
            raise LoginFailed(msg)

        if res <0:
            raise LoginFailed()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        if exc_val:
            msg=repr(exc_val)
            log.msg(msg)
            raise LoginFailed(msg)

    def step(self, challenge):
        return kerberos.authGSSServerStep(self.context, challenge)

    def response(self):
        return kerberos.authGSSServerResponse(self.context)

    def userName(self):
        return kerberos.authGSSServerUserName(self.context)

class NegotiateCredentialFactory(object):
    implements(ICredentialFactory)

    scheme = 'negotiate'

    def __init__(self, serviceType=''):
        self.serviceType = serviceType

    def getChallenge(self, request):
        return {}

    def decode(self, challenge, request):
        with ServerGSSContext(self.serviceType) as context:

            res=context.step(challenge)
            if res<0:
                raise LoginFailed()

            response = context.response()
            request.responseHeaders.addRawHeader(
                'www-authenticate', '{} {}'.format(self.scheme, response)
            )

            if res == kerberos.AUTH_GSS_COMPLETE:
                principal = context.userName()
                return NegotiateCredentials(principal)

        raise LoginFailed()

class NegotiateCredentialsChecker(object):
    implements(ICredentialsChecker)

    credentialInterfaces = (INegotiateCredentials,)

    def requestAvatarId(self, credentials):
        return credentials.principal
