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

    def new_nonce(self, controller):
        """ Set new nonce and send to the controller

        :param controller: controller id
        """
        log.debug('new_nonce()')
        controller.set_nonce(str(int(time.time())))
        controller.set_seq(0)
        controller.send_nonce()
        return

    def datagram_from_controller(self, host, datagram):
        """ Process incoming datagram

        :param host: Host instance of the sender
        :param datagram: datagram (str)
        """
        log.info('datagram_from_controller(%s): %s', \
            str(host), str(datagram))
        try:
            sdp = SDP.decode(datagram)
        except Exception as ex:
            log.error('sdp.decode() exception: %s', str(ex))
            raise Exception('sdp.decode() exception: ' + str(ex))

        ctrid = sdp.get_data('id')

        if ctrid is None:
            log.warning('invalid datagram, no id found!')
            raise Exception('invalid datagram, no id found!')

        controller = self._controllers.get_id(ctrid)
        if not controller:
            log.warning('Unknown controller: %s', ctrid)
            raise Exception('Unknown controller')
        log.debug('Controller: %s', str(controller))
        controller.set_host(host)
        self._check_signature(controller, sdp)
        log.debug('signature check passed')
        controller.set_last_sdp(sdp, ts=time.time())

    def _check_signature(self, controller, sdp):
        ctrid = controller.get_id()
        log.debug('_check_signature(%s)', ctrid)
        secret_key = controller.get_secret_key()
        log.debug('secret_key = %s', str(secret_key))
        if not sdp.is_signed():
            if secret_key:
                log.error('controller: %s datagram not signed', ctrid)
                raise Exception('sdp signature missing')
            else:
                log.debug('_check_signature passed without signature')
                return True
        if not secret_key:
            log.error('controller: %s secret_key not configured', ctrid)
            raise Exception('controller %s secret_key not configured', ctrid)
        nonce = controller.get_nonce()
        log.debug('nonce = %s', str(nonce))
        if not nonce:
            log.warning('controller: %s new_nonce', ctrid)
            self.new_nonce(controller)
            raise Exception('controller %s nonce updates' % ctrid)

        sdp.set_secret_key(secret_key)
        sdp.set_nonce(nonce)
        if not sdp.check_signature():
            log.error('controller: %s signature error', ctrid)
            self.new_nonce(controller)
            raise Exception('sdp signature error')
        self._check_seq(controller, sdp)
        log.debug('_check_signature passed')

    def _check_seq(self, controller, sdp):
        ctrid = controller.get_id()
        log.debug('_check_seq(%s)', ctrid)
        seq = None
        for part in sdp.gen_get():
            seq = part.get_in_seq()
        if seq == None:
            log.error('packet seq for %s is required for HMAC', ctrid)
            self.new_nonce(controller)
            raise Exception('packet seq is required for HMAC')
        prev_seq = controller.get_seq()
        if prev_seq:
            if not prev_seq < seq:
                log.error('seq is not growing for %s', ctrid)
                raise Exception('seq is not growing')
        controller.set_seq(seq)
