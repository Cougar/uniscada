""" WebSocket client data structure
"""
import json

import logging
log = logging.getLogger(__name__)   # pylint: disable=C0103
log.addHandler(logging.NullHandler())

class WsClient(object):
    """ One WebSocket client """
    def __init__(self, ws, listinstance=None):
        """ Create a new WebSocket client instance

        :param ws: WebSocket handler instance
        :param listinstance: optional WsClients instance
        """
        log.debug('Create a new WebSocket client (%s)', str(ws))
        self._id = ws
        self._listinstance = listinstance

    def get_id(self):
        """ Get id of WebSocket client

        :returns: WebSocket handler instance
        """
        return self._id

    def send_data(self, data):
        """ Send data as JSON string

        :param data: data
        """
        log.debug('send_data')
        self._id.write_message(json.dumps(data, indent=4, sort_keys=True))

    def __str__(self):
        return str(self._id)
