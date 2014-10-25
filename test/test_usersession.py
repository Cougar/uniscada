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
        self.usersession._userdata_callback = lambda: x.append('test')
        self.usersession._userdata_from_nagios(self.userdata)
        self.assertEqual(x[0], 'test')
        self.assertEqual(self.usersession.get_userdata(), self.userdata)

    def test_load_wrong_data(self):
        wronguserdata = self.userdata
        wronguserdata['user_name'] = 'WRONGUSER'
        self.assertRaises(Exception, self.usersession._userdata_from_nagios, wronguserdata)
        self.assertEqual(self.usersession.get_userdata(), None)
