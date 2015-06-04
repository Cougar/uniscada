""" Process datagrams from controllers
"""
import time

from sdp import SDP

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class SDPReceiver(object):
    """ Keep Controller instances updated with incoming data.

    When data arrives as a datagram (from UDP socket for instance),
    convert it to the SDP structure, find out sender Controller and
    update its internal state. Finally send ACK back to the Controller.
    """
    def __init__(self, core):
        """ SDP receiver instance.

        :param core: global Core instance
        """
        self._core = core
        self._controllers = self._core.controllers()
        self._servicegroups = self._core.servicegroups()
        self._msgbus = self._core.msgbus()

    def datagram_from_controller(self, host, datagram):
        """ Process incoming datagram

        :param host: Host instance of the sender
        :param datagram: datagram (str)
        """
        log.info('datagram_from_controller(%s): %s', \
            str(host), str(datagram))
        sdp = SDP()
        try:
            sdp.decode(datagram)
        except Exception as ex:
            log.error('sdp.decode() exception: %s', str(ex))
            raise Exception('sdp.decode() exception: ' + str(ex))

        ctrid = sdp.get_data('id')

        if ctrid is None:
            log.warning('invalid datagram, no id found!')
            raise Exception('invalid datagram, no id found!')

        controller = self._controllers.get_id(ctrid)
        if not controller:
            log.debug('Unknown controller: %s', ctrid)
            return
        controller.set_host(host)
        try:
            controller.set_last_sdp(sdp, ts=time.time())
        except Exception as ex:
            raise Exception('sdp set error: ' + str(ex))

        log.debug('Controller: %s', str(controller))
        controller.ack_last_sdp()
        log.debug("---------------------------------")

        r = {}
        r['resource'] = '/controllers/' + str(controller.get_id())
        r['body'] = controller.get_controller_data_v1()
        self._msgbus.publish(r['resource'], r)

        r = {}
        r['resource'] = '/hosts/' + str(controller.get_id())
        r['body'] = controller.get_host_data_v1(None)
        self._msgbus.publish(r['resource'], r)

        r = {}
        r['resource'] = '/services/' + str(controller.get_id())
        servicegroup = None
        setup = controller.get_setup()
        if setup:
            servicetable = setup.get('servicetable', None)
            if servicetable:
                servicegroup = self._servicegroups.get_id(servicetable)
        r['body'] = controller.get_service_data_v1_last_sdp(servicetable)
        self._msgbus.publish(r['resource'], r)
