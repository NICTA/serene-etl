from nose.tools import raises


@raises(AssertionError)
def test_ldap():
    from serene_proxy import sp_ldap
    user = sp_ldap.get_user('DOESNT EXIST')

def test_filter():
    from serene_proxy import sp_ldap
    from serene_proxy.make_filters import make_user_filters
    user = sp_ldap.LDAPUser(
        (
            'name=user@test.domain',
            dict(
                attrib=1
            ),
        )
    )

    assert user is not None, "LDAP did not find user"
    # filter_str = make_user_filters(user)
    # assert 'fq' in dict(filter_str)

if __name__ == "__main__":
    test_ldap()
