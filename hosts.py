''' Keep track of all hosts (devices) for Comm modules
'''

from globallist import GlobalList
from host import Host

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'Hosts', 'getMemberClass',
]

class Hosts(GlobalList):
    ''' List of all known hosts '''

    def __init__(self, storage=None, key=None):
        if storage and key:
            storage.delete(key)
        super(Hosts, self).__init__(storage=storage, key=key)

    def getMemberClass(self):
        return Host
