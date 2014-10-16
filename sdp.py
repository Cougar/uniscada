''' Message datagram composition and decomposition
    according to the Uniscada Service Description Protocol.
'''
import re

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'SDP',
    'add_keyvalue', 'add_status', 'add_value',
    'get_data', 'get_data_list', 'get_timestamp',
    'encode', 'decode',
]

class SDP(object):
    ''' Convert to and from SDP protocol datagram '''
    def __init__(self):
        self.data = {}
        self.data['data'] = {}
        self.data['float'] = {}
        self.data['status'] = {}
        self.data['value'] = {}
        self.data['query'] = {}

    def add_keyvalue(self, key, val):
        ''' Add key:val pair to the packet

        If val is "?", it is saved as a special query
        If key ends with "F", it is saved as a Float (hex str) - also TOV as legacy!
        If key ends with "S", it is saved as a Status (int [0 .. 3])
        If key ends with "V", it is saved as a Value (int, float or str)
        If key ends with "W", it is saved as a List of Values (str)
        All other keys are saved as Data (str)

        Data type conversion is caller responsibility. Only valid
        data types are accepted.

        :param key: data key
        :param val: data value
        '''
        if val == '?':
            self.data['query'][key] = '?'
        elif key[-1] == 'F' or key == 'TOV':
            if isinstance(val, str):
                self.data['float'][key] = val
            else:
                raise Exception('Value _MUST_BE_ hex str type')
        elif key[-1] == 'S':
            self.add_status(key[:-1], int(val))
        elif key[-1] == 'V':
            if val and \
               not isinstance(val, int) and \
               not isinstance(val, float) and \
               not isinstance(val, str):
                raise Exception('Value _MUST_BE_ str, int or float type')
            self.add_value(key[:-1], val)
        elif key[-1] == 'W':
            if not isinstance(val, str):
                raise Exception('List of Values _MUST_BE_ string of numbers')
            try:
                if val != ' '.join(list(map(str, (list(map(int, val.split(' '))))))):
                    raise Exception('Only integers allowed in List of Values')
            except:
                raise Exception('Only integers allowed in List of Values')
            self.add_value(key[:-1], list(map(int, val.split(' '))))
        else:
            if not isinstance(val, str):
                raise Exception('Data _MUST_BE_ string')
            self.data['data'][key] = val

    def add_status(self, key, val):
        ''' Add Status key:val pair to the packet

        :param key: Status key without "S" suffix
        :param val: Status value (int 0..3)
        '''
        if not isinstance(val, int):
            raise Exception('Status _MUST_BE_ int type')
        if val not in range(4):
            raise Exception('Status _MUST_BE_ between 0 and 3')
        self.data['status'][key] = int(val)

    def add_value(self, key, val):
        ''' Add Value or List of Values key:val pair to the packet

        :param key: Value or List of Values key without "V" or "W" suffix
        :param val: Value value (int, float or str) or List of Values value (list)
        '''
        if val and \
           not isinstance(val, int) and \
           not isinstance(val, float) and \
           not isinstance(val, str) and \
           not isinstance(val, list):
            raise Exception('Value _MUST_BE_ str, int, float or list type')
        self.data['value'][key] = val

    def get_data(self, key):
        ''' Get value of saved data

        :param key: data key

        If key ends with "S", it returns a Status (int)
        Hex float keys end with "F" (or key is "TOV"), returns hex float string
        If key ends with "V", it returns a Value (int, float or str)
        If key ends with "W", it returns a List of Values (list)
        All other keys returns a Data (str)

        :returns: Status, Value, List of Values, Data or None if key is missing
        '''
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
        ''' Generates (key, val) duples for all variables in the packet

        :returns: Generated (key, val) pair for each variable

        Status keys end with "S"
        Hex float keys end with "F" (except "TOV")
        Value keys end with "V"
        List of values keys end with "W"
        All other keys represent other Data

        Both key and value are always str type.
        '''
        for key in self.data['status'].keys():
            yield (key + 'S', str(self.data['status'][key]))
        for key in self.data['value'].keys():
            if isinstance(self.data['value'][key], list):
                yield (key + 'W', ' '.join(map(str, self.data['value'][key])))
            else:
                yield (key + 'V', str(self.data['value'][key]))
        for key in self.data['float'].keys():
            yield (key, self.data['float'][key])
        for key in self.data['data'].keys():
            yield (key, str(self.data['data'][key]))
        for key in self.data['query'].keys():
            yield (key, '?')

    def get_timestamp(self):
        ''' Read SDP timestamp from "in:<num>,<timestamp>"

        If "in" consists timestamp but the format has errors the
        Exception will be raised.

        :returns: timestamp or 'None' if not exists
        '''
        inn = str(self.get_data('in'))
        if not inn:
            return None
        p = re.compile('^\d+,(\d+(\.\d+)?)$')
        m = p.match(inn)
        if not m:
            return None
        return float(m.group(1))

    def encode(self, id=None):
        ''' Encodes SDP packet to datagram

        :param id: Optional paramater for id:<val> Data (str)

        :returns: The string representation of SDP datagram
        '''
        datagram = ''
        if id:
            self.add_keyvalue('id', id)
        if not 'id' in self.data['data']:
            log.error('id missing, cant encode')
            raise Exception("id missing");
        for key in self.data['data'].keys():
            datagram += key + ':' + str(self.data['data'][key]) + '\n'
        for key in self.data['float'].keys():
            datagram += key + ':' + str(self.data['float'][key]) + '\n'
        for key in self.data['status'].keys():
            datagram += key + 'S:' + str(self.data['status'][key]) + '\n'
        for key in self.data['value'].keys():
            if isinstance(self.data['value'][key], list):
                datagram += key + 'W:' + ' '.join(map(str, self.data['value'][key])) + '\n'
            else:
                datagram += key + 'V:' + str(self.data['value'][key]) + '\n'
        for key in self.data['query'].keys():
            datagram += key + ':?\n'
        return datagram

    def decode(self, datagram):
        ''' Decodes SDP datagram to packet

        :param datagram: The string representation of SDP datagram
        '''
        for line in datagram.splitlines():
            if line == '':
                log.warning('empty line in datagram')
                continue
            if not ':' in line:
                log.error('datagram line format error: no colon')
                raise Exception('datagram line error: \"' + line + '\"')
            try:
                (key, val) = line.split(':', 1)
            except:
                log.error('datagram line format error: cant split')
                raise Exception('error in line: \"' + line + '\"')
            if ':' in val:
                log.error('datagram line format error: more than one colon')
                raise Exception('colon in value: \"' + val + '\"')
            self.add_keyvalue(key, val)
        if self.get_data('id') is None:
            log.error('id missing in datagram')
            raise Exception('id: _MUST_ exists in datagram')

    def __str__(self):
        ''' Returns data dictionary '''
        return str(self.data)
