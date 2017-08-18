import ldap

from configuration import permission_multi_maps, permission_single_maps, ADDITIONAL_USER_NAME_PARTS
import configuration
domain = configuration.DOMAIN

dst_perm_list = permission_multi_maps.keys()   + permission_single_maps.keys()
src_perm_list = permission_multi_maps.values() + permission_single_maps.values()

class LDAPUser(object):
    def __init__(self, ldap_response):
        assert type(ldap_response) == tuple
        cn, attrs = ldap_response
        print cn, attrs
        if type(attrs) != dict:
            raise AssertionError('This response does not relate to a user')

        self.attrs = attrs
        self.names = {}
        if cn:
            for _ in cn.split(','):
                t, n = _.split('=')
                if t in self.names:
                    self.names[t] += '.{}'.format(n)
                else:
                    self.names[t] = n

    def get_permission(self, attr):
        """
        get the required attribute from the AD record and return it cleaned - ie no whitespace and UPPERCASE
        """

        assert attr in dst_perm_list, 'Permission not defined for mapping in configuration.py {}'.format(attr)

        multi = True
        try:
            src_perm = permission_multi_maps[attr]
        except KeyError:
            multi = False
            src_perm = permission_single_maps[attr]

        user_attr = self.attrs[src_perm]
        assert type(user_attr) == list
        cleaned_attr = [_.strip().upper() for _ in user_attr]

        if multi:
            #Could be an empty list
            return cleaned_attr
        else:
            if cleaned_attr:
                return cleaned_attr[0]
            else:
                return None

    @property
    def name(self):
        return '{CN}@{DC}'.format(**self.names)

    def __repr__(self):
        unp = [self.name]
        for _ in ADDITIONAL_USER_NAME_PARTS:
            try:
                unp.append('{}:{}'.format(_, self.get_permission(_).replace(' ', '+')))
            except KeyError:
                unp.append('{}:None'.format(_))

        return ' '.join(unp)


def get_user(user):
    username = configuration.LDAP_QUERY_USER
    password = configuration.LDAP_QUERY_PASS
    domain_controller = configuration.DOMAIN_CONTOLLER

    ld = ldap.initialize('ldap://' + domain_controller)
    ld.set_option(ldap.OPT_REFERRALS, 0)
    ld.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
    ld.simple_bind_s(username, password)

    users = []
    if '@' in user:
        user, u_domain = user.split('@')
        assert u_domain.upper() == domain.upper()

    base = configuration.LDAP_USER_SEARCH_BASE
    scope = ldap.SCOPE_SUBTREE
    filter_str = configuration.LDAP_USER_FILTER.format(user)

    for response in ld.search_s(base=base, scope=scope, filterstr=filter_str, attrlist=src_perm_list):
         try:
            users.append(LDAPUser(response))
         except AssertionError:
            pass

    assert len(users) == 1
    return users[0]
