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

    # Global lock for creating global Controllers instance
    _instance_lock = threading.Lock()

    @staticmethod
    def instance():
        ''' Returns a global `Controllers` instance.
        '''
        if not hasattr(Controllers, '_instance'):
            with Controllers._instance_lock:
                if not hasattr(Controllers, '_instance'):
                    Controllers._instance = Controllers()
        return Controllers._instance

    def getMemberClass(self):
        return Controller
