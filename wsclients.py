''' Keep track of all connected WebSocket clients
'''
import threading

from globallist import GlobalList
from wsclient import WsClient

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'WsClients', 'getMemberClass',
]

class WsClients(GlobalList):
    ''' List of all connected WebSocket clients '''

    def getMemberClass(self):
        return WsClient
