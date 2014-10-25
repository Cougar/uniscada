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

    def __init__(self):
        ''' User authorization data from Nagios

        Creating instance without reading any data from Nagios.
        To read user data from Nagios async_load_userdata()
        and/or getuserdata() needs to be called
        '''
        log.info('NagiosUser()')

    def async_load_userdata(self, user, data_callback):
        ''' Non-blocking Nagios data reader

        :param user: user name
        :param data_callback: call data_callback(data) when data arrived
        '''
        log.debug('_async_load_userdata()')
        if user == None:
            raise Exception('missing user')
        self._data_callback = data_callback
        tornado.httpclient.AsyncHTTPClient().fetch(self.__class__.baseurl + user, self._async_handle_request)

    def _async_handle_request(self, response):
        ''' Handle non-blocking Nagios data reader response
        '''
        log.info('_async_handle_request(%s)', str(response))
        if response.error:
            log.error('_async_handle_request(): Nagios data read error: %s', str(response.error))
            self._data_callback(None)
        try:
            userdata = json.loads(response.body.decode(encoding='UTF-8')).get('user_data', None)
            self._data_callback(userdata)
        except:
            raise SessionException('invalid nagios response')
            self._data_callback(None)

    def getuserdata(self, user):
        ''' Load user data from Nagios (blocking)

        :param user: user name

        :return: user data structure
        '''
        http_client = tornado.httpclient.HTTPClient()
        try:
            nagiosdata = http_client.fetch(self.__class__.baseurl + user).body.decode(encoding='UTF-8')
        except:
            raise SessionException('problem with nagios query: ' + str(sys.exc_info()[1]))
        http_client.close()
        try:
            jsondata = json.loads(nagiosdata)
        except:
            raise SessionException('problem with json: ' + str(sys.exc_info()[1]))
        try:
            if user != jsondata.get('user_data').get('user_name'):
                raise SessionException('invalid user name in nagios response')
        except:
            raise SessionException('invalid nagios response')
        return jsondata.get('user_data', None)


def main():
    if sys.argv.__len__() != 2:
        print("usage: %s <username>" % sys.argv[0])
        sys.exit(1)
    print(json.dumps(NagiosUser().getuserdata(sys.argv[1]), indent=4, sort_keys=True))

if __name__ == "__main__":
    main()
