""" Keep track of all connected WebSocket clients
"""

from globallist import GlobalList
from wsclient import WsClient

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class WsClients(GlobalList):
    """ List of all connected WebSocket clients """

    def getMemberClass(self):
        return WsClient
