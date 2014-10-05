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

    def getMemberClass(self):
        return UserSession
