''' Keep track of all known controllers
'''
import threading

from globallist import GlobalList
from controller import Controller

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'Controllers', 'getMemberClass',
]

class Controllers(GlobalList):
    ''' List of all known controllers '''

    def getMemberClass(self):
        return Controller
