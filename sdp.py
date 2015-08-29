"""Service Description Protocol.

Message datagram composition and decomposition
according to the Uniscada Service Description Protocol.
"""
import hmac
import hashlib
import base64

import re

from sdpexception import SDPException, SDPDecodeException

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class UnsecureSDP(object):
    """ Convert to and from SDP protocol datagram """
    def __init__(self, secret_key=None, nonce=None):
        """ Create a new empty in-memory ``SDP`` datagram
        """
        self._empty_sdp()

    def _empty_sdp(self):
        """ Clear all data from this SDP instance
        """
        self.data = {}
        self.data['data'] = {}
        self.data['float'] = {}
        self.data['status'] = {}
        self.data['value'] = {}
        self.data['query'] = {}

    def add_keyvalue(self, key, val):
        """ Add key:val pair to the packet

        * if val is "?", it is saved as a special query
        * if key ends with "F", it is saved as a Float (hex str)
          also TOV as legacy!
        * if key ends with "S", it is saved as a Status
          (int [0 .. 3] or str ['0' .. '3'])
        * if key ends with "V", it is saved as a Value (int, float or str)
        * if key ends with "W", it is saved as a List of Values (str)
        * all other keys are saved as Data (str)

        String 'null' is allowed in "V" and "W" keys and will be changed
        to None

        Data type conversion is caller responsibility. Only valid
        data types are accepted.

        :param key: data key
        :param val: data value
        """
        if val == '?':
            self._add_keyvalue_query(key)
        elif key[-1] == 'F' or key == 'TOV':
            self._add_keyvalue_floathex(key, val)
        elif key[-1] == 'S':
            self._add_keyvalue_status(key, val)
        elif key[-1] == 'V':
            self._add_keyvalue_value(key, val)
        elif key[-1] == 'W':
            self._add_keyvalue_values(key, val)
        else:
            self._add_keyvalue_string(key, val)

    def _add_keyvalue_query(self, key):
        """ Add special query key to the packet

        :param key: data key
        """
        self.data['query'][key] = '?'

    def _add_keyvalue_floathex(self, key, val):
        """ Add float key:val pair to the packet

        :param key: data key
        :param val: data value as float hex string
        """
        if isinstance(val, str):
            self.data['float'][key] = val
        else:
            raise SDPException('Value _MUST_BE_ hex str type')

    def _add_keyvalue_status(self, key, val):
        """ Add status key:val pair to the packet

        :param key: data key
        :param val: data value as status int or string
        """
        if isinstance(val, int):
            self.add_status(key[:-1], val)
        elif isinstance(val, str):
            if val in ['0', '1', '2', '3']:
                self.add_status(key[:-1], int(val))
            else:
                raise SDPException('Illegal Status value: ' + val)
        else:
            raise SDPException('Illegal Status type: ' + str(type(val)))

    def _add_keyvalue_value(self, key, val):
        """ Add single value key:val pair to the packet

        :param key: data key
        :param val: data value as status int, float or string
        """
        if val and \
           not isinstance(val, int) and \
           not isinstance(val, float) and \
           not isinstance(val, str):
            raise SDPException('Value _MUST_BE_ str, int or float type')
        self.add_value(key[:-1], val)

    def _add_keyvalue_values(self, key, val):
        """ Add single value key:val pair to the packet

        :param key: data key
        :param val: data values as string or list of numbers
        """
        if not isinstance(val, str) and \
           not isinstance(val, list):
            raise SDPException('List of Values _MUST_BE_ string' \
                'or list of numbers but ' + \
                str(key) + ' is ' + str(type(val)))
        if isinstance(val, list):
            val = ' '.join([_list_value_to_str(x) for x in val])
        lst = [_list_str_to_value(x) for x in val.split(' ')]
        if val != ' '.join([_list_value_to_str(x) for x in lst]):
            raise SDPException('Only integers allowed in List of ' \
                'Values: "' + val + '" != "' + \
                ' '.join([_list_value_to_str(x) for x in lst]) + '"')
        self.add_value(key[:-1], lst)

    def _add_keyvalue_string(self, key, val):
        """ Add single value key:val pair to the packet

        :param key: data key
        :param val: data values as string
        """
        if not isinstance(val, str):
            raise SDPException('Data _MUST_BE_ string')
        self.data['data'][key] = val

    def add_status(self, key, val):
        """ Add Status key:val pair to the packet

        :param key: Status key without "S" suffix
        :param val: Status value (int 0..3)
        """
        if not isinstance(val, int):
            raise SDPException('Status _MUST_BE_ int type')
        if val not in range(4):
            raise SDPException('Status _MUST_BE_ between 0 and 3')
        self.data['status'][key] = int(val)

    def add_value(self, key, val):
        """ Add Value or List of Values key:val pair to the packet

        :param key: Value or List of Values key without "V" or "W" suffix
        :param val: Value value (int, float or str) or
            List of Values value (list)
        """
        if val and \
           not isinstance(val, int) and \
           not isinstance(val, float) and \
           not isinstance(val, str) and \
           not isinstance(val, list):
            raise SDPException('Value _MUST_BE_ str, int, float or list type')
        self.data['value'][key] = val

    def get_data(self, key):    # pylint: disable=too-many-return-statements
        """ Get value of saved data

        :param key: data key

        * If key ends with "S", it returns a Status (int)
        * Hex float keys end with "F" (or key is "TOV"),
          returns hex float string
        * If key ends with "V", it returns a Value (int, float or str)
        * If key ends with "W", it returns a List of Values (list)
        * All other keys returns a Data (str)

        :returns: Status, Value, List of Values, Data or
        None if key is missing
        """
        if key in self.data['query']:
            return '?'
        elif key[-1] == 'F' or key == 'TOV':
            return self.data['float'].get(key, None)
        elif key[-1] == 'S':
            return self.data['status'].get(key[:-1], None)
        elif key[-1] == 'V':
            val = self.data['value'].get(key[:-1], None)
            if isinstance(val, list):
                return None
            return val
        elif key[-1] == 'W':
            val = self.data['value'].get(key[:-1], None)
            if isinstance(val, list):
                return val
            return None
        else:
            return self.data['data'].get(key, None)

    def get_data_list(self):
        """ Generates (key, val) duples for all variables in the packet

        :yields: Generated (key, val) pair for each variable

        * Status keys end with "S"
        * Hex float keys end with "F" (except "TOV")
        * Value keys end with "V"
        * List of values keys end with "W"
        * All other keys represent other Data

        Both key and value are always str type.
        """
        for key in self.data['status'].keys():
            yield (key + 'S', str(self.data['status'][key]))
        for key in self.data['value'].keys():
            if isinstance(self.data['value'][key], list):
                yield (key + 'W', \
                    ' '.join([str(x) for x in self.data['value'][key]]))
            else:
                yield (key + 'V', str(self.data['value'][key]))
        for key in self.data['float'].keys():
            yield (key, self.data['float'][key])
        for key in self.data['data'].keys():
            yield (key, str(self.data['data'][key]))
        for key in self.data['query'].keys():
            yield (key, '?')

    def get_in_seq(self):
        """ Read SDP sequence number from "in:<num>"

        :returns: sequence number or 'None' if not exists
        """
        inn = str(self.get_data('in'))
        if not inn:
            return None
        in_seq = re.compile(r'^(\d+)(,\d+(\.\d+)?)?$').match(inn)
        if not in_seq:
            return None
        return float(in_seq.group(1))

    def get_timestamp(self):
        """ Read SDP timestamp from "in:<num>,<timestamp>"

        If "in" consists timestamp but the format has errors the
        'Exception' will be raised.

        :returns: timestamp or 'None' if not exists
        """
        inn = str(self.get_data('in'))
        if not inn:
            return None
        is_ts = re.compile(r'^\d+,(\d+(\.\d+)?)$').match(inn)
        if not is_ts:
            return None
        return float(is_ts.group(1))

    def encode(self, controllerid=None):
        """ Encodes SDP packet to datagram

        :param controllerid: Optional paramater for id:<val> Data (str)

        :returns: The string representation of SDP datagram
        """
        datagram = ''
        if controllerid:
            self.add_keyvalue('id', controllerid)
        if not 'id' in self.data['data']:
            log.error('id missing, cant encode')
            raise SDPException("id missing")
        for key in self.data['data'].keys():
            datagram += key + ':' + str(self.data['data'][key]) + '\n'
        for key in self.data['float'].keys():
            datagram += key + ':' + str(self.data['float'][key]) + '\n'
        for key in self.data['status'].keys():
            datagram += key + 'S:' + str(self.data['status'][key]) + '\n'
        for key in self.data['value'].keys():
            if isinstance(self.data['value'][key], list):
                datagram += key + 'W:' + \
                    ' '.join([_list_value_to_str(x) \
                        for x in self.data['value'][key]]) + '\n'
            else:
                datagram += key + 'V:' + str(self.data['value'][key]) + '\n'
        for key in self.data['query'].keys():
            datagram += key + ':?\n'
        return datagram

    def decode(self, datagram):
        """ Decodes SDP datagram to packet

        :param datagram: The string representation of SDP datagram
        """
        for line in datagram.splitlines():
            if line == '':
                log.warning('empty line in datagram')
                continue
            if not ':' in line:
                log.error('datagram line format error: no colon')
                raise SDPDecodeException('datagram line error: \"' + \
                    line + '\"')
            try:
                (key, val) = line.split(':', 1)
            except:
                log.error('datagram line format error: cant split')
                raise SDPDecodeException('error in line: \"' + line + '\"')
            if ':' in val:
                log.error('datagram line format error: more than one colon')
                raise SDPDecodeException('colon in value: \"' + val + '\"')
            if not val:
                log.error('value mising for \"%s\"', key)
                raise SDPDecodeException('value mising for \"' + key + '\"')
            if not self.get_data('id') and key != 'id':
                raise SDPDecodeException('id MUST BE first line but read: %s\n%s' % (key, datagram))
            try:
                self.add_keyvalue(key, val)
            except SDPException as ex:
                self._empty_sdp()
                raise SDPDecodeException(ex)
        if self.get_data('id') is None:
            log.error('id missing in datagram')
            raise SDPDecodeException('id: _MUST_ exists in datagram')

    def __str__(self):
        """ Returns data dictionary """
        return str(self.data)

class SDP(UnsecureSDP):
    """ Convert to and from signed SDP protocol datagram """
    def __init__(self, secret_key=None, nonce=None):
        """ Create a new empty in-memory ``SDP`` datagram
        """
        super(SDP, self).__init__()
        self._secret_key = None
        self._nonce = None
        if secret_key:
            self.set_secret_key(secret_key)
        if nonce:
            self.set_nonce(nonce)

    def _empty_sdp(self):
        """ Clear all data from this SDP instance
        """
        super(SDP, self)._empty_sdp()
        self._signed = False

    def set_secret_key(self, secret_key):
        """ Set secret key for HMAC

        :param secret_key: secret key for HMAC
        """
        self._secret_key = secret_key.encode("UTF-8")

    def set_nonce(self, nonce):
        """ Set nonce key for HMAC

        :param nonce: nonce for HMAC calculation
        """
        self._nonce = nonce.encode("UTF-8")

    def is_signed(self):
        return self._signed

    def _add_keyvalue_string(self, key, val):
        """ Add single value key:val pair to the packet

        :param key: data key
        :param val: data values as string
        """
        if key == 'sha256':
            raise SDPException('"sha256" is not a valid key')
        super(SDP, self)._add_keyvalue_string(key, val)

    def encode(self, controllerid=None):
        """ Encodes SDP packet to datagram

        :param controllerid: Optional paramater for id:<val> Data (str)

        :returns: The string representation of SDP datagram
        """
        datagram = super(SDP, self).encode(controllerid)
        if self._secret_key:
            self.add_signature(datagram)
            datagram += 'sha256:' + self._sha256 + '\n'
        return datagram

    def add_signature(self, datagram):
        """ Add signature to SDP instance based on datagram string

        :param datagram: unsigned SDP datagram
        """
        if self._nonce == None:
            raise SDPDecodeException("nonce is required for HMAC")

        self._sha256 = self._calculate_signature(datagram)
        self._signed = True
        return

    def decode(self, datagram):
        """ Decodes SDP datagram to packet

        :param datagram: The string representation of SDP datagram
        """
        datagram_before_sig = ''
        for line in datagram.splitlines():
            if self._signed:
                log.error('no data is allowed after signature')
                raise SDPDecodeException('no data is allowed after signature')
            if not ':' in line:
                log.error('datagram line format error: no colon')
                raise SDPDecodeException('datagram line error: \"' + \
                    line + '\"')
            try:
                (key, val) = line.split(':', 1)
            except:
                log.error('datagram line format error: cant split')
                raise SDPDecodeException('error in line: \"' + line + '\"')
            if ':' in val:
                log.error('datagram line format error: more than one colon')
                raise SDPDecodeException('colon in value: \"' + val + '\"')
            if not val:
                log.error('value mising for \"%s\"', key)
                raise SDPDecodeException('value mising for \"' + key + '\"')
            if key == 'sha256':
                self._sha256 = val
                self._signed = True
                if not self._secret_key:
                    log.error('signed datagram from unsecure controller')
                    self._empty_sdp()
                    raise SDPDecodeException('signed datagram from unsecure controller')
                if not self.check_signature(datagram_before_sig):
                    self._empty_sdp()
                    return
                continue
            datagram_before_sig += line + '\n'
        super(SDP, self).decode(datagram_before_sig)

    def check_signature(self, datagram):
        if not self._signed:
            return False
        if not self._sha256:
            log.warning('SDP is not signed')
            return False
        signature = self._calculate_signature(datagram)
        return hmac.compare_digest(self._sha256, signature)

    def _calculate_signature(self, datagram):
        """ Return signature for given datagram

        :param datagram: Unsigned datagram

        :returns: BASE64 encoded signature
        """
        if not self._secret_key:
            log.error('secret key is not configured')
            raise SDPDecodeException('datagram is signed but ' \
                'secret key is not configured')
        if not self._nonce:
            log.error('nonce is not configured')
            raise SDPDecodeException('datagram is signed but ' \
                'nonce is not configured')
        return base64.b64encode( \
            hmac.new(self._secret_key, \
                msg=self._nonce+datagram.encode("UTF-8"), \
                digestmod=hashlib.sha256).digest()).decode()

def _list_str_to_value(string):
    """ Return int of string or None if string is "null" """
    if string == 'null':
        return None
    try:
        return int(string)
    except ValueError:
        raise SDPException('Illegal number in Value string: %s' \
            % string)

def _list_value_to_str(val):
    """ Return string or "null" if missing """
    if val is None:
        return 'null'
    return str(val)
