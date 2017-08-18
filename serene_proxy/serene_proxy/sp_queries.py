from make_filters import make_user_filters
from sp_ldap import get_user
from remote_log import splunk

ALLOWED_PARAMS = {
    'q': lambda k: True,
    'rows': lambda k: int(k) < 30000,
    'shards.tolerant': lambda k: True,
    'facet.field': lambda k: True,
    'facet': lambda k: True
}

REQUIRED_PARAMS = {
    'wt': lambda k: k=='json'
}


def check_query(q):
    q = q.strip()
    params = q.split(' ')

    for param in params:
        if ':' in param:
            field, term = param.split(':')
            if term == '*':
                return False

    return True


def check_params(params, user, uuid):
    assert type(params) == list
    for key, value in params:
        test = None

        if key in ALLOWED_PARAMS:
            test = ALLOWED_PARAMS[key]

        elif key in REQUIRED_PARAMS:
            test = REQUIRED_PARAMS[key]

        if (test and test(value) == False) or test is None:
            err = u'UUID={} {} = {} was not allowed'.format(uuid, key, value)
            splunk.mklog(user=user, action='uDENIED',details=err)
            raise ValueError(err)

    for req, test in REQUIRED_PARAMS.iteritems():
        candidates = filter(lambda k:k[0].lower() == req.lower(), params)
        if not candidates:
            err = u'UUID={} Required {} not specified'.format(uuid, req)
            splunk.mklog(user=user, action='uDENIED',details=err)
            raise ValueError(err)

        for key, value in candidates:
            if not test(value):
                err = u'UUID={} Required {} - {} did not satisfy'.format(uuid, key, value)
                splunk.mklog(user=user, action='uDENIED',details=err)
                raise ValueError(err)


def add_user_filters(user):
    return make_user_filters(get_user(user))
