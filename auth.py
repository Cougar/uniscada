'''
Auth authentication module

'''
from systemauth import SystemAuth
from cookieauth import CookieAuth

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'Auth',
]

class Auth(object):
    def __init__(self):
        ''' Auth authentication module '''
        self._authmodules = []

    def setup(self, config):
        ''' Auth configuration setup
        '''
        log.debug('setup()')
        self.setup_cookieauth(config)

    def setup_cookieauth(self, config):
        ''' Auth configuration setup for CookieAuth
        '''
        log.debug('setup_cookieauth()')
        if 'CookieAuth' in config:
            log.debug('CookieAuth setup')
            try:
                _auth = CookieAuth()
                cookiename = config.get('CookieAuth', 'cookiename')
                dbhost = config.get('CookieAuth', 'dbhost')
                dbname = config.get('CookieAuth', 'dbname')
                dbuser = config.get('CookieAuth', 'dbuser')
                dbpass = config.get('CookieAuth', 'dbpass')
                _auth.setup(cookiename, dbhost, dbuser, dbpass, dbname)
                self._authmodules.append(_auth)
            except configparser.NoSectionError:
                log.error('CookieAuth section is missing in config file')
            except KeyError as e:
                log.error('no %s defined for CookieAuth in config file', str(e))
            except Exception as e:
                log.critical('config error: %s', str(e))
        else:
            log.warning('CookieAuth configuration missing')

    def get_user(self, **kwargs):
        ''' Get authenticated username or None if missing

        :param **kwargs: parameters
        :returns: authenticated username or None
        '''
        log.debug('get_user(%s)', str(kwargs))
        for auth in self._authmodules:
            user = auth.get_user(**kwargs)
            if user:
                return user
        return None
