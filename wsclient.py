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
    def __init__(self, id):
        ''' Create a new WebSocket client instance

        :param id: WebSocket handler instance
        '''
        log.debug('Create a new WebSocket client (%s)', str(id))
        self._id = id

    def get_id(self):
        ''' Get id of WebSocket client

        :returns: WebSocket handler instance
        '''
        return self._id

    def __str__(self):
        return('id = ' + str(self._id))

