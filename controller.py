''' Controller data structure
'''
import time

from sdp import SDP
from stats import Stats

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'Controller',
    'get_id',
    'set_setup', 'get_setup',
    'set_host',
    'set_state_reg', 'get_state_register_list', 'get_state_reg',
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
        log.info('Create a new controller (%s)', str(id))
        self._id = id
        self._host = None
        self._state = {}
        self._state_ts = None
        self._last_sdp = None
        self._last_sdp_ts = None
        self._send_queue = {}
        self._setup = {}
        self._stats = Stats()

    def get_id(self):
        ''' Get id of controller

        :returns: controller id
        '''
        return self._id

    def set_setup(self, setup):
        ''' Set setup data

        :param setup: setup data
        '''
        self._setup = setup

    def get_setup(self):
        ''' Return setup data

        :returns: setup data
        '''
        return self._setup

    def set_host(self, host):
        ''' Assign Host instance to the controller

        :param data: Host instance
        '''
        if not self._host:
            log.debug('set_host(%s, %s): new', str(self._id), str(host))
        elif host == self._host:
            log.debug('set_host(%s, %s): already exists', str(self._id), str(host))
            return
        else:
            log.info('set_host(%s, %s): replace old host %s', str(self._id), str(host), str(self._host))
            self._host.del_controller(self)
        self._host = host
        self._host.add_controller(self)

    def set_state_reg(self, reg, val, ts = time.time()):
        ''' Set val of reg in the state dictionary of this controller

        :param reg: register name
        :param val: register value
        :param ts: optional timestamp
        '''
        log.debug('set_statereg(%s, %s, %s, %s)', str(self._id), str(reg), str(val), str(ts))
        self._state[reg] = { 'data': val, 'ts': ts }

    def get_state_register_list(self):
        ''' Generates (reg, val, ts) duples for all variables known
        for the controller

        :returns: Generated (reg, val, ts) duple for each register
        '''
        for reg in self._state.keys():
            yield (reg, self._state[reg]['data'], self._state[reg]['ts'])

    def get_state_reg(self, reg):
        ''' Get reg from the state dictionary of this controller

        :param reg: register name

        :returns: register (value, timestamp) duple or
        (None, None) if not exist
        '''
        if reg in self._state:
            log.debug('get_state_reg(%s, %s): (%s, %d)', str(self._id), str(reg), str(self._state[reg]['data']), self._state[reg]['ts'])
            return (self._state[reg]['data'], self._state[reg]['ts'])
        else:
            log.debug('get_state_reg(%s, %s): (None, None)', str(self._id), str(reg))
            return (None, None)

    def get_controller_data_v1(self):
        ''' Return controller data in API v1 format

        :returns: controller data in API v1 format
        '''
        r = {}
        r['controller'] = str(self._id)
        r['registers'] = []
        for (reg, val, ts) in self.get_state_register_list():
            r['registers'].append({ 'register': reg, 'value': val, 'timestamp': ts })
        return r

    def get_host_data_v1(self, isadmin):
        ''' Return host data in API v1 format

        :returns: host data in API v1 format
        '''
        r = {}
        r['controller'] = self._id
        if self._host:
            r['host'] = str(self._host.get_id())
        r['registers'] = []
        if self._last_sdp:
            for reg in self._last_sdp.get_data_list():
                r1 = {}
                r1['key'] = reg[0]
                r1['value'] = self._last_sdp.get_data(reg[0])
                r['registers'].append(r1)
        if self._last_sdp_ts:
            r['timestamp'] = self._last_sdp_ts
        if isadmin:
            r['stats'] = self._stats.get()
        return [r]

    def get_service_data_v1(self, servicegroup):
        ''' Return service data in API v1 format

        :returns: service data in API v1 format
        '''
        return self._get_service_data_v1(servicegroup)

    def get_service_data_v1_last_sdp(self, servicegroup):
        ''' Return service data in API v1 format

        Only changes by last incoming SDP datagramm will be returned

        :returns: service data in API v1 format
        '''
        if not self._last_sdp:
            return {}
        last_sdp_keys = []
        for reg in self._last_sdp.get_data_list():
                last_sdp_keys.append(reg[0])
        return self._get_service_data_v1(servicegroup, last_sdp_keys)

    def _get_service_data_v1(self, servicegroup, last_sdp_keys=None):
        r = {}
        r['host'] = self._id
        r['services'] = []
        if not servicegroup:
            return r
        services = servicegroup.get_services()
        if not services:
            return r
        for sta_reg in services.get_id_list():
            service = services.get_id(sta_reg)
            val_reg = None
            setup = service.get_setup()
            val_reg = setup.get('val_reg', None)
            if val_reg and val_reg != "":
                reg = val_reg
            else:
                reg = sta_reg
            log.debug('service sta_reg: %s, val_reg: %s, reg: %s' % (sta_reg, val_reg, reg))
            val_s, ts_s = self.get_state_reg(sta_reg)
            if val_s == None:
                log.debug('sta_reg=%s value is missing' % sta_reg)
                continue
            val, ts = self.get_state_reg(reg)
            if val == None:
                log.debug('reg=%s value is missing' % reg)
                continue
            if last_sdp_keys and not sta_reg in last_sdp_keys and not reg in last_sdp_keys:
                continue
            r1 = {}
            r1['key'] = reg
            conv_coef = setup.get('conv_coef', '')
            if conv_coef == '':
                if isinstance(val, list):
                    r1['value'] = list(map(str, val))
                else:
                    r1['value'] = str(val)
            else:
                conv_coef = int(conv_coef)
                if isinstance(val, list):
                    r1['value'] = [x / conv_coef for x in val]
                else:
                    r1['value'] = str(int(val) / conv_coef)
            r1['status'] = val_s
            r['services'].append(r1)
        if self._last_sdp_ts:
            r['timestamp'] = self._last_sdp_ts
        return r

    def set_last_sdp(self, sdp, ts = time.time()):
        ''' Remember last SDP packet and process it locally

        :param sdp: SDP instance
        :param ts: optional timestamp
        '''
        log.debug('set_last_sdp(%s)', str(self._id))
        try:
            self._process_incoming_sdp(sdp, ts = ts)
            self._last_sdp = sdp
            self._last_sdp_ts = ts
            self._stats.add('rx/sdp/ok', 1)
            self._stats.set('rx/sdp/last/timestamp', ts)
        except Exception as e:
            log.error('contoller=%s SDP processing error: %s', str(self._id),  str(e))
            self._stats.add('rx/sdp/errors/total', 1)
            raise Exception(e)

    def _process_incoming_sdp(self, sdp, ts = time.time()):
        ''' Process SDP packet from controller:

        - check if controller sent timestamp too
        - check if packet is still valid if timestamp exists
        - update state dictionary and the send queue

        :param sdp: SDP instance
        :param ts: optional timestamp of SDP packet
        '''
        log.debug('_process_incoming_sdp(%s)', str(self._id))

        if not sdp:
            return
        sdpts = sdp.get_timestamp()
        if sdpts:
            now = time.time()
            log.debug('timestamp read from datagram: %s', str(sdpts))
            if sdpts > now:
                # FIXME: drop such packets
                log.warning('%s sent packet from the future (%d sec)', str(self._id), int(sdpts - now))
                self._stats.add('rx/sdp/errors/future', 1)
                raise Exception('packet has future timestamp')
            if (now - sdpts) > 60 * 60 * 24 * 7:  # TODO: config param
                # FIXME: drop such packets
                log.warning('ignoring too old timestamp from %s: %d, now=%d', str(self._id), int(sdpts), int(now))
                self._stats.add('rx/sdp/errors/too_old', 1)
                raise Exception('packet timestamp is too old')
            ts = sdpts
        if self._state_ts:
            if ts < self._state_ts:
                log.info('old state ts=%d, new ts=%d', self._state_ts, ts)
                self._stats.add('rx/sdp/errors/older_than_previous', 1)
                raise Exception('SDP packet is older than previous, ignoring')
        self._update_state_from_sdp(sdp, ts)
        self._state_ts = ts

    def _update_state_from_sdp(self, sdp, ts = time.time()):
        ''' Read last SDP packet and update state dictionary

        - update state dictionary
        - remove seen registers from the send queue

        :param sdp: SDP instance
        :param ts: optional timestamp of SDP packet
        '''
        log.debug('_update_state_from_sdp(%s)', str(self._id))
        for (register, value) in sdp.get_data_list():
            if register == 'id' or register == 'in':
                continue
            if value == '?':
                self.send_queue_add_last_reg(register)
                self._stats.add('rx/sdp/requests', 1)
            else:
                self.set_state_reg(register, sdp.get_data(register), ts = ts)
                self.send_queue_remove_reg(register, value)

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
        if self._last_sdp:
            inn = self._last_sdp.get_data('in')
            if inn:
                ack.add_keyvalue('in', inn)
        for reg in self._send_queue.keys():
            ack.add_keyvalue(reg, self._send_queue[reg])
            self._stats.add('tx/sdp/updates', 1)
        self._host.send(ack.encode())
        self._stats.add('tx/ack', 1)

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
        (val, ts) = self.get_state_reg(reg)
        if val:
            log.debug('  %s', str(val))
            self._send_queue[reg] = val

    def send_queue_remove_reg(self, reg, val):
        ''' Remove one register from send queue

        :param reg: register to remove
        :param val: expected register value
        '''
        expval = self._send_queue.get(reg, None)
        if not expval:
            return
        log.debug('send_queue_remove_reg(%s, %s)', str(self._id), str(reg))
        if expval != val:
            log.warning('controller=%s reg=%s val=\"%s\" != sent val=\"%s\"', str(self._id), str(reg), str(val), str(expval))
            self._stats.add('rx/sdp/updates/different', 1)
            return
        else:
            self._send_queue.pop(reg)
            self._stats.add('rx/sdp/updates/accepted', 1)

    def __getstate__(self):
        state = self.__dict__.copy()
        state['_host'] = None
        state['_send_queue'] = {}
        return state

    def __str__(self):
        return(str(self._id) + ': ' +
               'host = ' + str(self._host) +
               ', setup = ' + str(self._setup) +
               ', state = ' + str(self._state) +
               ', send_queue = ' + str(self._send_queue))
