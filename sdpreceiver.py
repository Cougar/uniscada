''' Process datagrams from controllers
'''
import time

from sdp import SDP
from controllers import Controllers

import logging
log = logging.getLogger(__name__)

class SDPReceiver(object):
    ''' Keep Controller instances updated with incoming data.

    When datagram arrives as a datagram (from UDP socket for instance),
    convert it to the SDP structure, find out sender Controller and
    update its internal state. Finally send ACK back to the Controller.
    '''
    def __init__(self):
        ''' SDP receiver instance.
        '''
        self._controllers = Controllers.instance()

    def datagram_from_controller(self, host, datagram):
        ''' Process incoming datagram

        :param host: Host instance for the sender
        :param datagram: datagram (str)
        '''
        log.info('datagram_from_controller(%s): %s', str(host), str(datagram))
        sdp = SDP()
        sdp.decode(datagram)

        id = sdp.get_data('id')

        if id is None:
            log.warning('invalid datagram, no id found!')
            return

        controller = self._controllers.find_controller(id)
        controller.set_host(host)
        controller.set_last_sdp(sdp, ts = time.time())

        log.debug('Controller: ' + str(controller))
        controller.ack_last_sdp()
        log.debug("---------------------------------")
