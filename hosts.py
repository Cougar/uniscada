''' Keep track of all hosts (devices) for Comm modules
'''
import threading

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

    def getMemberClass(self):
        return Host
