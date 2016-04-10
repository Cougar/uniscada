""" Controller data structure
"""
import time

from sdp import SDP
from sdpexception import SDPException
from stats import Stats

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class Controller(object):
    """ One controller """
    def __init__(self, ctrid, listinstance=None):
        """ Create new controller instance

        :param ctrid: controller id
        :param listinstance: optional Controllers instance
        """
        log.info('Create a new controller (%s)', str(ctrid))
        self._id = ctrid
        self._host = None
        self._state = {}
        self._state_ts = None
        self._last_sdp = None
        self._last_sdp_ts = None
        self._send_queue = {}
        self._setup = {}
        self._stats = Stats()
        self._nonce = None
        self._seq = None
        self._servicegroups = None
        self._msgbus = None

    def get_id(self):
        """ Get id of controller

        :returns: controller id
        """
        return self._id

    def set_servicegroups(self, servicegroups):
        """ Set servicegroups

        :param servicegroups: servicegroups
        """
        self._servicegroups = servicegroups

    def get_servicegroups(self):
        """ Return servicegroups

        :returns: servicegroups
        """
        return self._servicegroups

    def set_msgbus(self, msgbus):
        """ Set msgbus

        :param msgbus: msgbus
        """
        self._msgbus = msgbus

    def get_msgbus(self):
        """ Return msgbus

        :returns: msgbus
        """
        return self._msgbus

    def set_setup(self, setup):
        """ Set setup data

        :param setup: setup data
        """
        self._setup = setup

    def get_setup(self):
        """ Return setup data

        :returns: setup data
        """
        return self._setup

    def get_secret_key(self):
        """ Get controller secret key used for SHA256 HMAC signature

        :returns: secret key
        """
        if not self._setup:
            return None
        return self._setup.get('secret_key', None)

    def get_nonce(self):
        """ Get controller nonce used for SHA256 HMAC signature

        :returns: nonce
        """
        return self._nonce

    def set_nonce(self, nonce):
        """ Set controller nonce used for SHA256 HMAC signature

        :param nonce: nonce
        """
        self._nonce = nonce

    def get_seq(self):
        """ Get sequence num for HMAC calculation

        Sequence numbers MUST BE always increasing as long 'nonce' is
        unchanged.

        :returns: sequence num
        """
        if not self._seq:
            self._seq = 0
        return self._seq

    def set_seq(self, seq):
        """ Set controller packet sequence num

        :param seq: sequence num
        """
        self._seq = seq

    def set_host(self, host):
        """ Assign Host instance to the controller

        :param data: Host instance
        """
        if not self._host:
            log.debug('set_host(%s, %s): new', str(self._id), str(host))
        elif host == self._host:
            log.debug('set_host(%s, %s): already exists', \
                str(self._id), str(host))
            return
        else:
            log.info('set_host(%s, %s): replace old host %s', \
                str(self._id), str(host), str(self._host))
            self._host.del_controller(self)
        self._host = host
        self._host.add_controller(self)

    def set_state_reg(self, reg, val, ts=time.time()):
        """ Set val of reg in the state dictionary of this controller

        :param reg: register name
        :param val: register value
        :param ts: optional timestamp
        """
        log.debug('set_statereg(%s, %s, %s, %s)', \
            str(self._id), str(reg), str(val), str(ts))
        self._state[reg] = {'data': val, 'ts': ts}

    def get_state_register_list(self):
        """ Generates (reg, val, ts) duples for all variables known
        for the controller

        :returns: Generated (reg, val, ts) duple for each register
        """
        for reg in self._state.keys():
            yield (reg, self._state[reg]['data'], self._state[reg]['ts'])

    def get_state_reg(self, reg):
        """ Get reg from the state dictionary of this controller

        :param reg: register name

        :returns: register (value, timestamp) duple or
        (None, None) if not exist
        """
        if reg in self._state:
            log.debug('get_state_reg(%s, %s): (%s, %d)', \
                str(self._id), str(reg), \
                str(self._state[reg]['data']), self._state[reg]['ts'])
            return (self._state[reg]['data'], self._state[reg]['ts'])
        else:
            log.debug('get_state_reg(%s, %s): (None, None)', \
                str(self._id), str(reg))
            return (None, None)

    def get_controller_data_v1(self):
        """ Return controller data in API v1 format

        :returns: controller data in API v1 format
        """
        r = {}
        r['controller'] = str(self._id)
        r['registers'] = []
        for (reg, val, ts) in self.get_state_register_list():
            r['registers'].append( \
                {'register': reg, 'value': val, 'timestamp': ts})
        return r

    def get_host_data_v1(self, check_scope):
        """ Return host data in API v1 format

        :returns: host data in API v1 format
        """
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
        if check_scope and check_scope('stats:controller'):
            r['stats'] = self._stats.get()
        return r

    def get_service_data_v1(self, servicegroup):
        """ Return service data in API v1 format

        :returns: service data in API v1 format
        """
        return self._get_service_data_v1(servicegroup)

    def get_service_data_v1_last_sdp(self, servicegroup):
        """ Return service data in API v1 format

        Only changes by last incoming SDP datagramm will be returned

        :returns: service data in API v1 format
        """
        if not self._last_sdp:
            return {}
        last_sdp_keys = []
        for reg in self._last_sdp.get_data_list():
            last_sdp_keys.append(reg[0])
        return self._get_service_data_v1(servicegroup, last_sdp_keys)

    def _get_service_data_v1(self, servicegroup, last_sdp_keys=None):
        """ Return service data in API v1 format

        If last_sdp_keys is set then return only these keys

        :returns: service data in API v1 format
        """
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
            log.debug('service sta_reg: %s, val_reg: %s, reg: %s', \
                sta_reg, val_reg, reg)
            val_s, _ = self.get_state_reg(sta_reg)
            if val_s == None:
                log.debug('sta_reg=%s value is missing', sta_reg)
                continue
            val, _ = self.get_state_reg(reg)
            if val == None:
                log.debug('reg=%s value is missing', reg)
                continue
            if last_sdp_keys and not sta_reg in last_sdp_keys \
                    and not reg in last_sdp_keys:
                continue
            r1 = {}
            r1['key'] = reg
            conv_coef = setup.get('conv_coef', '')
            if conv_coef == '':
                if isinstance(val, list):
                    r1['value'] = [str(x) for x in val]
                else:
                    r1['value'] = str(val)
            else:
                conv_coef = float(conv_coef)
                if isinstance(val, list):
                    r1['value'] = [x / conv_coef for x in val]
                else:
                    r1['value'] = str(float(val) / conv_coef)
            r1['status'] = val_s
            r['services'].append(r1)
        if self._last_sdp_ts:
            r['timestamp'] = self._last_sdp_ts
        return r

    def set_last_sdp(self, sdp, ts=time.time()):
        """ Remember last SDP packet and process it locally

        :param sdp: SDP instance
        :param ts: optional timestamp
        """
        log.debug('set_last_sdp(%s)', str(self._id))
        try:
            self._process_incoming_sdp(sdp, ts=ts)
        except SDPException as ex:
            log.error('contoller=%s SDP processing error: %s', \
                str(self._id),  str(ex))
            self._stats.set('rx/sdp/last_error/reason', str(ex))
            self._stats.add('rx/sdp/errors/total', 1)
            raise SDPException(ex)
        except Exception as ex:
            log.exception('contoller=%s SDP processing error: %s', \
                str(self._id),  str(ex))
        self._last_sdp = sdp
        self._last_sdp_ts = ts
        self._stats.add('rx/sdp/ok', 1)
        self._stats.set('rx/sdp/last/timestamp', ts)
        self._publish()
        self.ack_last_sdp()

    def _process_incoming_sdp(self, sdp, ts=time.time()):
        """ Process SDP packet from controller:

        - check if controller sent timestamp too
        - check if packet is still valid if timestamp exists
        - update state dictionary and the send queue

        :param sdp: SDP instance
        :param ts: optional timestamp of SDP packet
        """
        log.debug('_process_incoming_sdp(%s)', str(self._id))

        if not sdp:
            return
        sdpts = sdp.get_timestamp()
        if sdpts:
            now = time.time()
            log.debug('timestamp read from datagram: %s', str(sdpts))
            if sdpts > (now + 60):
                # FIXME: drop such packets
                log.warning('%s sent packet from the future (%d sec)', \
                    str(self._id), int(sdpts - now))
                self._stats.add('rx/sdp/errors/future', 1)
                raise Exception('packet has future timestamp')
            if (now - sdpts) > 60 * 60 * 24 * 7:  # TODO: config param
                # FIXME: drop such packets
                log.warning('ignoring too old timestamp from %s: ' \
                    '%d, now=%d', str(self._id), int(sdpts), int(now))
                self._stats.add('rx/sdp/errors/too_old', 1)
                raise Exception('packet timestamp is too old')
            ts = sdpts
        if self._state_ts:
            if ts < self._state_ts:
                log.info('old state ts=%d, new ts=%d', self._state_ts, ts)
                self._stats.add('rx/sdp/errors/older_than_previous', 1)
                raise Exception('SDP packet is older than previous,' \
                    ' ignoring')
        self._update_state_from_sdp(sdp, ts)
        self._state_ts = ts

    def _publish(self):
        """ Publish new data to other modules """
        r = {}
        r['resource'] = '/controllers/' + self._id
        r['body'] = [ self.get_controller_data_v1() ]
        self._msgbus.publish(r['resource'], r)

        r = {}
        r['resource'] = '/hosts/' + self._id
        r['body'] = [ self.get_host_data_v1(None) ]
        self._msgbus.publish(r['resource'], r)

        r = {}
        r['resource'] = '/services/' + self._id
        servicegroup = None
        if self._setup:
            servicetable = self._setup.get('servicetable', None)
            if servicetable:
                servicegroup = self._servicegroups.get_id(servicetable)
        r['body'] = [ self.get_service_data_v1_last_sdp(servicegroup) ]
        if len(r['body'][0]['services']):
            self._msgbus.publish(r['resource'], r)


    def _update_state_from_sdp(self, sdp, ts=time.time()):
        """ Read last SDP packet and update state dictionary

        - update state dictionary
        - remove seen registers from the send queue

        :param sdp: SDP instance
        :param ts: optional timestamp of SDP packet
        """
        log.debug('_update_state_from_sdp(%s)', str(self._id))
        for (register, value) in sdp.get_data_list():
            if register == 'id' or register == 'in':
                continue
            if value == '?':
                self.send_queue_add_last_reg(register)
                self._stats.add('rx/sdp/requests', 1)
            else:
                self.set_state_reg(register, sdp.get_data(register), \
                    ts=ts)
                self.send_queue_remove_reg(register, value)

    def send_nonce(self):
        """ Send nonce to controller

        Nonce packet consists only "id" and "nonce" fields
        """
        log.debug('send_nonce(%s)', str(self._id))

        nonce = self.get_nonce()
        if not nonce:
            log.error('Cant send nonce if it is missing')
            return
        sdp = SDP(secret_key=self.get_secret_key(), nonce=nonce)
        sdp.add_keyvalue('id', self._id)
        sdp.add_keyvalue('nonce', nonce)
        self._host.send(sdp.encode())
        self._stats.add('tx/nonce', 1)

    def ack_last_sdp(self):
        """ Send ACK based on the last SDP packet.

        ACK packet consists "id", "in" if it was defined in the last
        SDP packet and register values from the send queue
        """
        log.debug('ack_last_sdp(%s)', str(self._id))
        if not self._host:
            log.error('No host data for controller (%s)', str(self._id))
            return
        if not self._last_sdp:
            log.error('Last SDP missing')
            return
        ack = SDP()
        ack.add_keyvalue('id', self._id)
        part_ack = None
        for part in self._last_sdp.gen_get():
            if part_ack:
                ack += part_ack
                part_ack = None
            inn = part.get_data('in')
            if inn:
                part_ack = SDP()
                part_ack.add_keyvalue('in', inn)
            self._stats.add('tx/sdp/ack/parts', 1)
        if part_ack:
            self._stats.add('tx/sdp/ack/updates', self._add_send_queue_to_sdp(part_ack))
        else:
            self._stats.add('tx/sdp/ack/updates', self._add_send_queue_to_sdp(ack))
        if part_ack:
            ack += part_ack
        ack.set_secret_key(self.get_secret_key())
        ack.set_nonce(self.get_nonce())
        self._host.send(ack.encode())
        self._stats.add('tx/sdp/ack/packets', 1)

    def send_settings(self):
        """ Send SDP with register values from the send queue
        """
        log.debug('send_settings(%s)', str(self._id))
        if not self._host:
            log.error('No host data for controller (%s)', str(self._id))
            return
        sdp = SDP()
        sdp.add_keyvalue('id', self._id)
        self._stats.add('tx/sdp/conf/updates', self._add_send_queue_to_sdp(sdp))
        self._host.send(sdp.encode())
        self._stats.add('tx/sdp/conf/packets', 1)

    def _add_send_queue_to_sdp(self, sdp):
        """ Add register values from the send queue
        """
        changes = 0
        for reg in self._send_queue.keys():
            sdp.add_keyvalue(reg, self._send_queue[reg]['val'])
            changes += 1
        self._stats.add('tx/sdp/confreg', changes)
        return changes

    def send_queue_reset(self):
        """ Reset send queue
        """
        log.debug('send_queue_reset(%s)', str(self._id))
        self._send_queue = {}

    def send_queue_add_last_reg(self, reg):
        """ Add known register to the send queue

        :param reg: register to add the the queue
        """
        log.debug('send_queue_add_last_reg(%s, %s)', str(self._id), str(reg))
        (val, ts) = self.get_state_reg(reg)
        self.send_queue_add_reg_val(reg, val)

    def send_queue_add_reg_val(self, reg, val):
        """ Add a register and value to the send queue

        :param reg: register to add the the queue
        :param val: register value
        """
        log.debug('send_queue_add_reg_val(%s, %s, %s)', str(self._id), str(reg), str(val))
        if val:
            log.debug('  %s', str(val))
            self._send_queue[reg] = {}
            self._send_queue[reg]['val'] = val
            self._send_queue[reg]['tries'] = 0

    def send_queue_remove_reg(self, reg, val):
        """ Remove one register from send queue

        :param reg: register to remove
        :param val: expected register value (string)
        """
        expval = self._send_queue.get(reg, {}).get('val', None)
        if not expval:
            return
        if isinstance(expval, list):
            expval = ' '.join([SDP._list_value_to_str(x) for x in expval])
        log.debug('send_queue_remove_reg(%s, %s)', str(self._id), str(reg))
        if expval != val:
            log.warning('controller=%s reg=%s val=\"%s\" != ' \
                'sent val=\"%s\"', str(self._id), str(reg), \
                str(val), str(expval))
            self._stats.add('rx/sdp/updates/different', 1)
            self._send_queue[reg]['tries'] += 1
            if self._send_queue[reg]['tries'] > 10:
                log.warning('controller=%s reg=%s expired', str(self._id), str(reg))
                self._stats.add('rx/sdp/updates/expired', 1)
                self._send_queue.pop(reg)
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
