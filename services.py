''' All services of one servicegroup
'''

from globallist import GlobalList
from service import Service

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'Services', 'getMemberClass',
]

class Services(GlobalList):
    ''' List of all services of one servicegroup '''

    def getMemberClass(self):
        return Service

