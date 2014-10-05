''' Controller data structure
'''

from sdp import SDP

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'Controller',
    'get_id',
    'set_host',
    'set_state_reg', 'get_state_reg',
    'set_last_sdp', 'ack_last_sdp',
    'send_queue_reset', 'send_queue_add_last_reg', 'send_queue_remove_reg',
]

class Controller(object):
    ''' One controller '''
    def __init__(self, id, listinstance = None):
        ''' Create new controller instance

        :param id: controller id
        :param listinstance: optional Controllers instance
        '''
        log.debug('Create a new controller (%s)', str(id))
        self._id = id
        self._host = None
        self._state = {}
        self._last_sdp = None
        self._send_queue = {}

    def get_id(self):
        ''' Get id of controller

        :returns: controller id
        '''
        return self._id

    def set_host(self, host):
        ''' Assign Host instance to the controller

        :param data: Host instance
        '''
        if not self._host:
            log.debug('set_host(%s, %s): new', str(self._id), str(host))
        elif host != self._host:
            log.info('set_host(%s, %s): replace old host %s', str(self._id), str(host), str(self._host))
            self._host.remove()
        else:
            log.info('set_host(%s, %s): already exists', str(self._id), str(host))
            return
        self._host = host

    def set_state_reg(self, reg, val, ts = None):
        ''' Set val of reg in the state dictionary of this controller

        :param reg: register name
        :param val: register value
        :param ts: optional timestamp
        '''
        log.debug('set_statereg(%s, %s, %s, %s)', str(self._id), str(reg), str(val), str(ts))
        self._state[reg] = { 'data': val, 'ts': ts }

    def get_state_reg(self, reg):
        ''' Get reg from the state dictionary of this controller

        :param reg: register name

        :returns: register value or None if not exist
        '''
        if reg in self._state:
            log.debug('get_state_reg(%s, %s): %s', str(self._id), str(reg), str(self._state[reg]['data']))
            return self._state[reg]['data']
        else:
            log.debug('get_state_reg(%s, %s): None', str(self._id), str(reg))
            return None

    def set_last_sdp(self, sdp, ts = None):
        ''' Remember last SDP packet and process it locally

        :param sdp: SDP instance
        :param ts: optional timestamp
        '''
        log.debug('set_last_sdp(%s)', str(self._id))
        self._last_sdp = sdp
        self._process_incoming_sdp(sdp, ts = ts)

    def _process_incoming_sdp(self, sdp, ts = None):
        ''' Process SDP packet from controller:

        - update state dictionary
        - remove seen registers from the send queue

        :param sdp: SDP instance
        :param ts: optional timestamp
        '''
        log.debug('_process_incoming_sdp(%s)', str(self._id))
        for (register, value) in self._last_sdp.get_data_list():
            if register == 'id' or register == 'in':
                continue
            if '?' in value:
                self.send_queue_add_last_reg(register)
            else:
                self.set_state_reg(register, value, ts = ts)
                self.send_queue_remove_reg(register)

    def ack_last_sdp(self):
        ''' Send ACK based on the last SDP packet.

        ACK packet consists "id", "in" if it was defined in the last
        SDP packet and register values from the send queue
        '''
        log.debug('ack_last_sdp(%s)', str(self._id))
        if not self._host:
            log.error('No host data for controller (%s)', str(self._id))
            return

        ack = SDP()
        ack.add_keyvalue('id', self._id)
        inn = self._last_sdp.get_data('in')
        if inn is not None:
            ack.add_keyvalue('in', inn)
        for reg in self._send_queue.keys():
            ack.add_keyvalue(reg, self._send_queue[reg])
        self._host.send(ack.encode())

    def send_queue_reset(self):
        ''' Reset send queue
        '''
        log.debug('send_queue_reset(%s)', str(self._id))
        self._send_queue = {}

    def send_queue_add_last_reg(self, reg):
        ''' Add known register to the send queue

        :param reg: register to add the the queue
        '''
        log.debug('send_queue_add_last_reg(%s, %s)', str(self._id), str(reg))
        val = self.get_state_reg(reg)
        if val:
            log.debug('  %s', str(val))
            self._send_queue[reg] = val

    def send_queue_remove_reg(self, reg):
        ''' Remove one register from send queue

        :param reg: register to remove
        '''
        log.debug('send_queue_remove_reg(%s, %s)', str(self._id), str(reg))
        self._send_queue.pop(reg, None)

    def __str__(self):
        return(str(self._id) + ': ' +
               'host = ' + str(self._host) +
               ', state = ' + str(self._state) +
               ', send_queue = ' + str(self._send_queue))
