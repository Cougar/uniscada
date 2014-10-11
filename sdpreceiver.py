''' Process datagrams from controllers
'''
import time

from sdp import SDP
from controllers import Controllers

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class SDPReceiver(object):
    ''' Keep Controller instances updated with incoming data.

    When data arrives as a datagram (from UDP socket for instance),
    convert it to the SDP structure, find out sender Controller and
    update its internal state. Finally send ACK back to the Controller.
    '''
    def __init__(self, controllers):
        ''' SDP receiver instance.

        :param controllers: global Controllers instance
        '''
        self._controllers = controllers

    def datagram_from_controller(self, host, datagram):
        ''' Process incoming datagram

        :param host: Host instance of the sender
        :param datagram: datagram (str)
        '''
        log.info('datagram_from_controller(%s): %s', str(host), str(datagram))
        sdp = SDP()
        sdp.decode(datagram)

        id = sdp.get_data('id')

        if id is None:
            log.warning('invalid datagram, no id found!')
            return

        controller = self._controllers.find_by_id(id)
        controller.set_host(host)
        controller.set_last_sdp(sdp, ts = time.time())

        log.debug('Controller: ' + str(controller))
        controller.ack_last_sdp()
        log.debug("---------------------------------")
