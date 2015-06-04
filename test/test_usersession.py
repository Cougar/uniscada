import unittest

from usersession import UserSession

class UserSessionTest(unittest.TestCase):
    '''
    This is the unittest for the uniscada.usersession module
    '''
    def setUp(self):
        self.usersession = UserSession('testuser')
        self.userdata = {
                "user_name":"testuser",
                "user_groups":{
                    "testgroup":{},
                    "kvv":{
                        "112233445566":"controller1",
                        "010203040506":"controller2",
                        "0123456789AB":"controller3"
                        }
                    },
                "hostgroups":{
                    "testgroup":{
                        "alias":"testgroup",
                        "members":{
                            "112233445566":"controller1",
                            "010203040506":"controller2",
                            "0123456789AB":"controller3",
                            "0A1B2C3D4E5F":"controller4"
                            }
                        }
                    }
                }

    def test_init(self):
        self.assertEqual(self.usersession.get_id(), 'testuser')
        self.assertEqual(self.usersession.get_userdata(), None)

    def test_load_data_callback(self):
        x = []
        def _cb(usersession):
                x.append(usersession)
        self.usersession._userdata_callback = _cb
        self.usersession._userdata_from_nagios(self.userdata)
        self.assertEqual(x[0], self.usersession)
        self.assertEqual(self.usersession.get_userdata(), self.userdata)

    def test_load_wrong_data(self):
        wronguserdata = self.userdata
        wronguserdata['user_name'] = 'WRONGUSER'
        self.usersession._userdata_from_nagios(wronguserdata)
        self.assertEqual(self.usersession.get_userdata(), None)

    def test_user_access_ok(self):
        self.usersession._userdata_from_nagios(self.userdata)
        self.assertEqual(True, self.usersession.check_access('112233445566'))

    def test_user_access_fail_nouser(self):
        self.assertEqual(False, self.usersession.check_access('112233445566'))

    def test_user_access_fail_noaccess(self):
        self.usersession._userdata_from_nagios(self.userdata)
        self.assertEqual(False, self.usersession.check_access('0A1B2C3D4E5F'))
        self.assertEqual(False, self.usersession.check_access('000000000000'))
    def test_adminuser(self):
        self.usersession._userdata_from_nagios(self.userdata)
        self.assertEqual(False, self.usersession.is_admin())
        self.usersession.set_admin()
        self.assertEqual(True, self.usersession.is_admin())

    def test_adminuser_access(self):
        self.usersession._userdata_from_nagios(self.userdata)
        self.usersession.set_admin()
        self.assertEqual(True, self.usersession.check_access('112233445566'))
        self.assertEqual(True, self.usersession.check_access('0A1B2C3D4E5F'))
        self.assertEqual(True, self.usersession.check_access('000000000000'))

    def test_scopes(self):
        self.assertFalse(self.usersession.check_scope(''))
        self.assertFalse(self.usersession.check_scope('test'))
        self.assertFalse(self.usersession.check_scope('test:x'))
        self.assertFalse(self.usersession.check_scope('test:y'))
        self.usersession.add_scope('test:x')
        self.assertFalse(self.usersession.check_scope(''))
        self.assertFalse(self.usersession.check_scope('test'))
        self.assertTrue(self.usersession.check_scope('test:x'))
        self.assertFalse(self.usersession.check_scope('test:y'))
        self.usersession.add_scope('test')
        self.assertFalse(self.usersession.check_scope(''))
        self.assertTrue(self.usersession.check_scope('test'))
        self.assertTrue(self.usersession.check_scope('test:x'))
        self.assertTrue(self.usersession.check_scope('test:y'))
