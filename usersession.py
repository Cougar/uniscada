''' User data structure
'''

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'UserSession',
    'get_id',
]

class UserSession(object):
    ''' One user '''
    def __init__(self, id, listinstance = None):
        ''' Create new user instance

        :param id: user id (username)
        :param listinstance: optional UserSessions instance
        '''
        log.debug('Create a new user (%s)', str(id))
        self._id = id

    def get_id(self):
        ''' Get id of user (username)

        :returns: user id (username)
        '''
        return self._id

    def __str__(self):
        return(str(self._id))
