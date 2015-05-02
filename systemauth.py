'''
SystemAuth authentication module

This module checks 'X-ApiKey' header and gives full access for the cli tools
'''

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'SystemAuth',
]

class SystemAuth(object):

    def __init__(self):
        ''' SystemAuth authentication module '''

    def setup(self, core):
        ''' SystemAuth configuration setup

        :param core: Core instance
        '''
        log.debug('setup()')
        _usersession = core.usersessions().find_by_id('_system_')
        _usersession._set_userdata({'user_name': '_system_'})
        _usersession.set_admin()

    def get_user(self, **kwargs):
        ''' Get authenticated username or None if missing

        parameters in **kwargs:
            host: caller host name

        :param **kwargs: parameters
        :returns: authenticated username or None
        '''
        log.debug('get_user(%s)', str(kwargs))
        # FIXME X-ApiKey check missing
        host = kwargs.get('host', None)
        if host == "127.0.0.1":
            return('_system_')
        return None
