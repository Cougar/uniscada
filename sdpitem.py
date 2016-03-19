"""Service Description Protocol.

Message datagram composition and decomposition
according to the Uniscada Service Description Protocol.
"""
import re

from sdpexception import SDPException, SDPDecodeException

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class SDPItem(object):
    """ Convert to and from SDP protocol datagram """
    def __init__(self, secret_key=None, nonce=None):
        """ Create a new empty in-memory ``SDP`` datagram
        """
        self._empty_sdp()

    def _empty_sdp(self):
        """ Clear all data from this SDP instance
        """
        self.data = {}
        self.data['id'] = None
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
        if key == 'id':
            self.data['id'] = val
        elif val == '?':
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
        if not isinstance(val, str):
            raise SDPException('Value _MUST_BE_ hex str type')
        if val == '':
            raise SDPException('Float value _MUST_ exist')
        self.data['float'][key] = val

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
            val = ' '.join([SDPItem._list_value_to_str(x)
                            for x in val])
        lst = [SDPItem._list_str_to_value(x) for x in val.split(' ')]
        if val != ' '.join([SDPItem._list_value_to_str(x) for x in lst]):
            raise SDPException('Only integers allowed in List of ' \
                'Values: "' + val + '" != "' + \
                ' '.join([SDPItem._list_value_to_str(x)
                          for x in lst]) + '"')
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
        if key == 'id':
            return self.data.get('id', None)
        elif key in self.data['query']:
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
        if self.data['id']:
            yield ('id', self.data['id'])
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
        return int(in_seq.group(1))

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

    def remove_data(self, key):    # pylint: disable=too-many-return-statements
        """ Remove entry of saved data

        :param key: data key to remove
        """
        if key == 'id':
            self.data['id'] = None
            return

        if not self.get_data(key):
            raise SDPException('no such key exists')

        if key in self.data['query']:
            del self.data['query'][key]
        elif key[-1] == 'F' or key == 'TOV':
            del self.data['float'][key]
        elif key[-1] == 'S':
            del self.data['status'][key[:-1]]
        elif key[-1] == 'V':
            del self.data['value'][key[:-1]]
        elif key[-1] == 'W':
            del self.data['value'][key[:-1]]
        else:
            del self.data['data'][key]

    def gen_get(self):
        """ Return this SDP

        :returns: Generator of this single SDP
        """
        return (sdp for sdp in [self])

    def encode(self, controllerid=None):
        """ Encodes SDP packet to datagram

        :param controllerid: Optional paramater for id:<val> Data (str)

        :returns: The string representation of SDP datagram
        """
        datagram = ''
        if controllerid:
            self.add_keyvalue('id', controllerid)
        if not self.data['id']:
            log.error('id missing, cant encode')
            raise SDPException("id missing")
        if self.data['id']:
            datagram += 'id:' + str(self.data['id']) + '\n'
        datagram += self._encode_data()
        return datagram

    def _encode_data(self):
        """ Encodes SDP packet data part

        :returns: The string representation of SDP datagram data part
        """
        datagram = ''
        if 'in' in self.data['data']:
            datagram += 'in:' + str(self.data['data']['in']) + '\n'
        for key in self.data['data'].keys():
            if key != 'in':
                datagram += key + ':' + str(self.data['data'][key]) + '\n'
        for key in self.data['float'].keys():
            datagram += key + ':' + str(self.data['float'][key]) + '\n'
        for key in self.data['status'].keys():
            datagram += key + 'S:' + str(self.data['status'][key]) + '\n'
        for key in self.data['value'].keys():
            if isinstance(self.data['value'][key], list):
                datagram += key + 'W:' + \
                    ' '.join([SDPItem._list_value_to_str(x)
                              for x in self.data['value'][key]]) + '\n'
            else:
                datagram += key + 'V:' + str(self.data['value'][key]) + '\n'
        for key in self.data['query'].keys():
            datagram += key + ':?\n'
        return datagram

    @staticmethod
    def _decode_line(line):
        """ Decodes one line from SDP packet

        :param line: one line from SDP packet

        :returns: (key, val) duple
        """
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
            val = ''

        return (key, val)

    @classmethod
    def decode(cls, datagram, sdp=None):
        """ Decodes SDP datagram to packet

        :param datagram: The string representation of SDP datagram
        """
        controllerid = None
        if not sdp:
            sdp = SDPItem()
        for line in datagram.splitlines():
            if line == '':
                log.warning('empty line in datagram')
                continue
            (key, val) = SDPItem._decode_line(line)
            if key == 'id':
                if controllerid:
                    raise SDPDecodeException('ONLY ONE "id" is allowed')
                controllerid = val
            if sdp.get_data(key):
                raise SDPDecodeException('multiple "%s" fields' % key)
            try:
                sdp.add_keyvalue(key, val)
            except SDPException as ex:
                raise SDPDecodeException(ex)
            if not controllerid:
                raise SDPDecodeException('id MUST BE first line but read: %s\n%s' % (key, datagram))
        if not controllerid:
            log.error('id missing in datagram')
            raise SDPDecodeException('id: _MUST_ exists in datagram')
        return sdp

    def __str__(self):
        """ Returns data dictionary """
        return str(self.data)

    @staticmethod
    def _list_str_to_value(string):
        """ Return int of string or None if string is "null" """
        if string == 'null':
            return None
        if string == '':
            raise SDPException('Empty string is not allowed')
        try:
            return int(string)
        except ValueError:
            raise SDPException('Illegal number in Value string: %s' \
                % string)

    @staticmethod
    def _list_value_to_str(val):
        """ Return string or "null" if missing """
        if val is None:
            return 'null'
        return str(val)
