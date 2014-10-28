''' Keep track of all servicegroups
'''

from globallist import GlobalList
from servicegroup import ServiceGroup

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'ServiceGroups', 'getMemberClass',
]

class ServiceGroups(GlobalList):
    ''' List of all servicegroups '''

    def getMemberClass(self):
        return ServiceGroup
