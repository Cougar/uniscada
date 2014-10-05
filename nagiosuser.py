''' Nagios communication for user autorization
'''

import sys
import tornado.httpclient
import json

from sessionexception import SessionException

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'NagiosUser',
    'async_load_userdata',
    'getuserdata',
]

class NagiosUser:
    ''' Nagios user data reader
    '''
    baseurl = 'https://n.itvilla.com/get_user_data?user_name='

    def __init__(self, user):
        ''' User authorization data from Nagios

        Creating instance do not get eny data from Nagios. To read user
        data from Nagios async_load_userdata() and/or getuserdata()
        needs to be called

        :param user: user name
        '''
        log.info('NagiosUser(%s)', str(user))
        if user == None:
            raise Exception('missing user')
        self.user = user
        self._userdata = None

    def async_load_userdata(self, data_callback):
        ''' Non-blocking Nagios data reader

        :param data_callback: call data_callback(data) when data arrived
        '''
        log.debug('_async_load_userdata()')
        self._data_callback = data_callback
        tornado.httpclient.AsyncHTTPClient().fetch(self.__class__.baseurl + self.user, self._async_handle_request)

    def _async_handle_request(self, response):
        ''' Handle non-blocking Nagios data reader response
        '''
        log.info('_async_handle_request(): ' + str(response))
        if response.error:
            log.error('_async_handle_request(): Nagios data read error: ' + str(response.error))
            self._data_callback(None)
        else:
            self._userdata = json.loads(response.body.decode(encoding='UTF-8')).get('user_data', None)
            self._data_callback(self._userdata)

    def _sync_load_userdata(self):
        ''' Load user data from Nagios (blocking)
        '''
        http_client = tornado.httpclient.HTTPClient()
        try:
            nagiosdata = http_client.fetch(self.__class__.baseurl + self.user).body.decode(encoding='UTF-8')
        except:
            raise SessionException('problem with nagios query: ' + str(sys.exc_info()[1]))
        http_client.close()
        try:
            jsondata = json.loads(nagiosdata)
        except:
            raise SessionException('problem with json: ' + str(sys.exc_info()[1]))
        try:
            if self.user != jsondata.get('user_data').get('user_name'):
                raise SessionException('invalid user name in nagios response')
        except:
            raise SessionException('invalid nagios response')
        self._userdata = jsondata.get('user_data', None)

    def getuserdata(self):
        ''' Return user data

        If userdata missing then load it (blocking)

        :return: user data structure
        '''
        if not self._userdata:
            self._sync_load_userdata()
        if not self._userdata:
            raise SessionException('user data missing')
        return self._userdata

    def __str__(self):
        return(str(self.user) + ': userdata = ' + str(self._userdata))
