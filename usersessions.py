''' Keep track of all known users
'''

from globallist import GlobalList
from usersession import UserSession

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'UserSessions', 'getMemberClass',
]

class UserSessions(GlobalList):
    ''' List of all known users '''

    def __init__(self, storage=None, key=None):
        if storage and key:
            storage.delete(key)
        super(UserSessions, self).__init__(storage=storage, key=key)

    def getMemberClass(self):
        return UserSession
