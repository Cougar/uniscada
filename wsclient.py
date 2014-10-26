''' WebSocket client data structure
'''
import json

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'WsClient',
    'get_id',
]

class WsClient(object):
    ''' One WebSocket client '''
    def __init__(self, id, listinstance = None):
        ''' Create a new WebSocket client instance

        :param id: WebSocket handler instance
        :param listinstance: optional WsClients instance
        '''
        log.debug('Create a new WebSocket client (%s)', str(id))
        self._id = id

    def get_id(self):
        ''' Get id of WebSocket client

        :returns: WebSocket handler instance
        '''
        return self._id

    def send_data(self, data):
        log.debug('send_data')
        self._id.write_message(json.dumps(data, indent=4, sort_keys=True))

    def __str__(self):
        return(str(self._id))
