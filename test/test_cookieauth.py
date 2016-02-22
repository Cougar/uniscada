import unittest

import time
from mock import patch, MagicMock

class UserSessionTest(unittest.TestCase):
    '''
    This is the unittest for the uniscada.usersession module
    '''
    def setUp(self):
        self.mysql_connect_cursor_mock = MagicMock()
        self.mysql_connect_cursor_mock.execute.return_value = None
        self.mysql_connect_cursor_mock.close.return_value = None
        self.mysql_connect_mock = MagicMock()
        self.mysql_connect_mock.cursor.return_value = self.mysql_connect_cursor_mock
        self.mysql_connector_mock = MagicMock()
        self.mysql_connector_mock.connect.return_value = self.mysql_connect_mock
        self.mysql_mock = MagicMock()
        self.mysql_mock.connector = self.mysql_connector_mock
        modules = {
            'mysql': self.mysql_mock,
            'mysql.connector': self.mysql_connector_mock
        }
        self.module_patcher = patch.dict('sys.modules', modules)
        self.module_patcher.start()
        from cookieauth import CookieAuth
        self.cookieauth = CookieAuth()
        self.cookiename = None

    def _getcookie(self, cookiename):
        self.cookiename = cookiename
        return self.cookie

    def test_cookieauth(self):
        ''' Test cookieauth '''
        self.mysql_connect_cursor_mock.__iter__.return_value = list([[1, 'wrong_secret', time.time() + 9], [99, '71bc3e0142ea528ea247696fadb10063', time.time() + 1]]).__iter__()
        self.cookieauth.setup('cookiename', 'dbhost', 'dbuser', 'dbpass' ,'dbname')
        self.mysql_mock.connector.connect.assert_called_once_with(host='dbhost', user='dbuser', password='dbpass', database='dbname')
        self.assertEqual(self.cookieauth._conn, self.mysql_connect_mock)
        ''' test user validation from valid cookie '''
        self.cookie = 'username:99:bfb929cf8851efd136e01da3eff36207'
        self.assertEqual(self.cookieauth.get_user(cookiehandler=self._getcookie), 'username')
        self.assertEqual(self.cookiename, 'cookiename')
        ''' test user validation from invalid cookie '''
        self.cookie = 'username:99:00000000000000000000000000000000'
        self.assertEqual(self.cookieauth.get_user(cookiehandler=self._getcookie), None)
        self.cookie = 'username'
        self.assertEqual(self.cookieauth.get_user(cookiehandler=self._getcookie), None)
        ''' test user validation from missing cookie '''
        self.cookie = ''
        self.assertEqual(self.cookieauth.get_user(cookiehandler=self._getcookie), None)
        ''' test md5 hashes '''
        self.assertTrue(self.cookieauth.check_cookie_md5('username:99:bfb929cf8851efd136e01da3eff36207'))
        self.assertFalse(self.cookieauth.check_cookie_md5('username:66:bfb929cf8851efd136e01da3eff36207'))
        self.assertFalse(self.cookieauth.check_cookie_md5('username:99:00000000000000000000000000000000'))
        self.assertFalse(self.cookieauth.check_cookie_md5('username:66'))
        self.assertFalse(self.cookieauth.check_cookie_md5('username'))
        self.assertFalse(self.cookieauth.check_cookie_md5(''))
        ''' test expired secret keys '''
        time.sleep(1)
        self.assertEqual(self.cookieauth.get_user(cookiehandler=self._getcookie), None)
        self.assertFalse(self.cookieauth.check_cookie_md5('username:99:bfb929cf8851efd136e01da3eff36207'))
