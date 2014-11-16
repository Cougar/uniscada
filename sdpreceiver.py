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
    def __init__(self, core):
        ''' SDP receiver instance.

        :param core: global Core instance
        '''
        self._core = core
        self._controllers = self._core.controllers()
        self._msgbus = self._core.msgbus()

    def datagram_from_controller(self, host, datagram):
        ''' Process incoming datagram

        :param host: Host instance of the sender
        :param datagram: datagram (str)
        '''
        log.info('datagram_from_controller(%s): %s', str(host), str(datagram))
        sdp = SDP()
        try:
            sdp.decode(datagram)
        except Exception as e:
            log.error('sdp.decode() exception: %s', str(e))
            raise Exception('sdp.decode() exception: ' + str(e))

        id = sdp.get_data('id')

        if id is None:
            log.warning('invalid datagram, no id found!')
            raise Exception('invalid datagram, no id found!')

        controller = self._controllers.find_by_id(id)
        controller.set_host(host)
        try:
            controller.set_last_sdp(sdp, ts = time.time())
        except Exception as e:
            raise Exception('sdp set error: ' + str(e))

        log.debug('Controller: %s', str(controller))
        controller.ack_last_sdp()
        log.debug("---------------------------------")

        r = {}
        r['resource'] = '/controllers/' + str(controller.get_id())
        r['body'] = controller.get_controller_data_v1()
        self._msgbus.publish(r['resource'], r)

        r = {}
        r['resource'] = '/hosts/' + str(controller.get_id())
        r['body'] = controller.get_host_data_v1()
        self._msgbus.publish(r['resource'], r)

        r = {}
        r['resource'] = '/services/' + str(controller.get_id())
        r['body'] = controller.get_service_data_v1_last_sdp()
        self._msgbus.publish(r['resource'], r)
