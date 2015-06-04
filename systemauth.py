"""
SystemAuth authentication module

This module checks 'X-ApiKey' header and gives full access for the cli tools
"""

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class SystemAuth(object):
    """ System access authentication module """

    SYSTEMUSER = '_system_'

    def __init__(self):
        """ SystemAuth authentication module """

    def setup(self, core):
        """ SystemAuth configuration setup

        :param core: Core instance
        """
        log.debug('setup()')
        _usersession = core.usersessions().find_by_id(self.SYSTEMUSER)
        _usersession._set_userdata({'user_name': self.SYSTEMUSER})
        _usersession.add_scope('system')
        _usersession.add_scope('all')
        _usersession.add_scope('stats')

    def get_user(self, **kwargs):
        """ Get authenticated username or None if missing

        parameters in **kwargs:
            host: caller host name

        :param **kwargs: parameters
        :returns: authenticated username or None
        """
        log.debug('get_user(%s)', str(kwargs))
        # FIXME X-ApiKey check missing
        host = kwargs.get('host', None)
        if host == "127.0.0.1":
            return self.SYSTEMUSER
        return None
