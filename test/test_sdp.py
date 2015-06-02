import unittest

from sdp import SDP
from sdpexception import SDPException, SDPDecodeException

class SDPTests(unittest.TestCase):
    '''
    This is the unittest for the uniscada.sdp module
    '''
    def setUp(self):
        self.sdp = SDP()

    def test_get_data_missing(self):
        ''' Test getting missing keys '''
        self.assertEqual(self.sdp.get_data('AAS'), None)
        self.assertEqual(self.sdp.get_data('ABV'), None)
        self.assertEqual(self.sdp.get_data('id'), None)

    def test_add_keyvalue_status(self):
        ''' Test setting/getting key:val for Status '''
        self.sdp.add_keyvalue('AAS', 2)
        d = self.sdp.get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 2)
        self.assertEqual(self.sdp.get_data('AAs'), None)
        self.assertEqual(self.sdp.get_data('aaS'), None)

        self.sdp.add_keyvalue('ABS', '3')
        d = self.sdp.get_data('ABS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 3)

        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AxS', -1)
        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AyS', 4)
        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AqS', '4')
        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AXS', 'a')
        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AYS', [1, 2])
        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AZS', None)

    def test_add_status(self):
        ''' Test setting/getting Status key:val '''
        self.sdp.add_status('AA', 2)
        d = self.sdp.get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 2)
        self.assertEqual(self.sdp.get_data('AAs'), None)
        self.assertEqual(self.sdp.get_data('aaS'), None)

        self.assertRaises(SDPException, self.sdp.add_status, 'AX', 'a')
        self.assertRaises(SDPException, self.sdp.add_status, 'AY', [1, 2])
        self.assertRaises(SDPException, self.sdp.add_status, 'AZ', None)

    def test_add_keyvalue_value(self):
        ''' Test setting/getting key:val for Value '''
        self.sdp.add_keyvalue('AAV', 1234)
        d = self.sdp.get_data('AAV')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 1234)
        self.assertEqual(self.sdp.get_data('AAv'), None)
        self.assertEqual(self.sdp.get_data('aaV'), None)

        self.sdp.add_keyvalue('ABV', 1.5)
        d = self.sdp.get_data('ABV')
        self.assertTrue(isinstance(d, float))
        self.assertEqual(d, 1.5)

        self.sdp.add_keyvalue('ACV', 'abc')
        d = self.sdp.get_data('ACV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc')

        self.sdp.add_keyvalue('ADV', 'cde xyz')
        d = self.sdp.get_data('ADV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'cde xyz')

        self.sdp.add_keyvalue('AEV', '1 2 3.5')
        d = self.sdp.get_data('AEV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '1 2 3.5')

        self.sdp.add_keyvalue('AFV', 'not null string')
        d = self.sdp.get_data('AFV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'not null string')

        self.sdp.add_keyvalue('AGV', 'null')
        self.assertEqual(self.sdp.get_data('AGV'), 'null')

        self.sdp.add_keyvalue('AHV', '')
        self.assertEqual(self.sdp.get_data('AHV'), '')

        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AXV', [1, 2])

    def test_add_keyvalue_values_list(self):
        ''' Test setting/getting key:val for List of Values (list) '''
        self.sdp.add_keyvalue('AAW', [1])
        d = self.sdp.get_data('AAW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1])
        self.assertEqual(self.sdp.get_data('AAw'), None)
        self.assertEqual(self.sdp.get_data('aaW'), None)

        self.sdp.add_keyvalue('ABW', [1, None, 2])
        d = self.sdp.get_data('ABW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1, None, 2])

        self.assertRaises(SDPException, self.sdp.add_keyvalue, \
            'AXV', [0, None, 3.5])

    def test_add_keyvalue_values(self):
        ''' Test setting/getting key:val for List of Values '''
        self.sdp.add_keyvalue('AAW', '1')
        d = self.sdp.get_data('AAW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1])
        self.assertEqual(self.sdp.get_data('AAw'), None)
        self.assertEqual(self.sdp.get_data('aaW'), None)

        self.sdp.add_keyvalue('ABW', '1 2 35')
        d = self.sdp.get_data('ABW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1, 2, 35])

        self.sdp.add_keyvalue('ACW', '0 null 35')
        d = self.sdp.get_data('ACW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [0, None, 35])

        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AXW', 1)
        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AYW', 1.5)
        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AZW', 'a')
        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AQW', '')
        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AWW', None)
        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'AVW', [1.5])

    def test_add_value(self):
        ''' Test setting/getting Value and List of Values key:val '''
        self.sdp.add_value('AA', 1234)
        d = self.sdp.get_data('AAV')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 1234)
        self.assertEqual(self.sdp.get_data('AAv'), None)
        self.assertEqual(self.sdp.get_data('aaV'), None)
        self.assertEqual(self.sdp.get_data('AAS'), None)
        self.assertEqual(self.sdp.get_data('AAW'), None)

        self.sdp.add_value('AB', 1.5)
        d = self.sdp.get_data('ABV')
        self.assertTrue(isinstance(d, float))
        self.assertEqual(d, 1.5)

        self.sdp.add_value('AC', 'value')
        d = self.sdp.get_data('ACV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'value')

        self.sdp.add_value('AD', [1])
        d = self.sdp.get_data('ADW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1])

        self.sdp.add_value('AE', [1, 2, 3])
        d = self.sdp.get_data('AEW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1, 2, 3])

        self.sdp.add_value('AF', None)
        self.assertEqual(self.sdp.get_data('AFV'), None)
        self.assertEqual(self.sdp.get_data('AFW'), None)

        self.sdp.add_value('AG', [1, None, 3])
        d = self.sdp.get_data('AGW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1, None, 3])

    def test_add_keyvalue_data(self):
        ''' Test setting/getting key:val for Other Data '''
        self.sdp.add_keyvalue('aa', '123')
        d = self.sdp.get_data('aa')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '123')
        self.assertEqual(self.sdp.get_data('AA'), None)
        self.assertEqual(self.sdp.get_data('a'), None)
        self.assertEqual(self.sdp.get_data('aaa'), None)

        self.sdp.add_keyvalue('ab', 'null')
        d = self.sdp.get_data('ab')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'null')

        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'ax', 1)
        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'ay', 1.5)
        self.assertRaises(SDPException, self.sdp.add_keyvalue, 'az', [1, 2])

    def test_add_keyvalue_request_data(self):
        ''' Test setting/getting key:val where val == '?' '''
        self.sdp.add_keyvalue('AAS', '?')
        d = self.sdp.get_data('AAS')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        self.sdp.add_keyvalue('ABV', '?')
        d = self.sdp.get_data('ABV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        self.sdp.add_keyvalue('ACW', '?')
        d = self.sdp.get_data('ACW')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

    def test_timestamp(self):
        ''' Test get_timestamp() method '''
        self.assertEqual(self.sdp.get_timestamp(), None)
        self.sdp.add_keyvalue('in', '1')
        self.assertEqual(self.sdp.get_timestamp(), None)
        self.sdp.add_keyvalue('in', '2,123')
        self.assertEqual(self.sdp.get_timestamp(), 123)
        self.sdp.add_keyvalue('in', '3,456.7')
        self.assertEqual(self.sdp.get_timestamp(), 456.7)
        self.sdp.add_keyvalue('in', '4,567,89')
        self.assertEqual(self.sdp.get_timestamp(), None)
        self.sdp.add_keyvalue('in', '5,67.8.9')
        self.assertEqual(self.sdp.get_timestamp(), None)

    def test_encode_with_id(self):
        ''' Test encoder for full packet'''
        self.sdp.add_keyvalue('id', 'abc123')
        self.sdp.add_keyvalue('ip', '10.0.0.10')
        self.sdp.add_keyvalue('AAS', 1)
        self.sdp.add_keyvalue('ABV', 2)
        self.sdp.add_keyvalue('ACV', 3.5)
        self.sdp.add_keyvalue('ADV', '4')
        self.sdp.add_keyvalue('AEV', '5.5')
        self.sdp.add_keyvalue('AFV', 'abc')
        self.sdp.add_keyvalue('AGW', '4')
        self.sdp.add_keyvalue('AHW', '5 6 75')
        self.sdp.add_keyvalue('AIS', '?')
        self.sdp.add_keyvalue('AJV', '?')
        self.sdp.add_keyvalue('AKW', '?')
        self.sdp.add_keyvalue('iq', '?')
        self.sdp.add_keyvalue('TOV', '4000D3349FEBBEAE') # legacy
        self.sdp.add_keyvalue('ALF', '4000D3349FEBBEAE')
        self.sdp.add_keyvalue('AMW', '8 null 9')
        datagram = self.sdp.encode()
        self.assertTrue(isinstance(datagram, str))
        self.assertEqual(sorted(datagram.splitlines()), [
            'AAS:1',
            'ABV:2',
            'ACV:3.5',
            'ADV:4',
            'AEV:5.5',
            'AFV:abc',
            'AGW:4',
            'AHW:5 6 75',
            'AIS:?',
            'AJV:?',
            'AKW:?',
            'ALF:4000D3349FEBBEAE',
            'AMW:8 null 9',
            'TOV:4000D3349FEBBEAE',
            'id:abc123',
            'ip:10.0.0.10',
            'iq:?',
        ])

    def test_encode_with_id_param(self):
        ''' Test encoder with id for full packet'''
        self.sdp.add_keyvalue('id', 'abc123')
        self.sdp.add_keyvalue('ip', '10.0.0.10')
        self.sdp.add_keyvalue('AAS', 1)
        self.sdp.add_keyvalue('ABV', 2)
        self.sdp.add_keyvalue('ACV', 3.5)
        self.sdp.add_keyvalue('ADV', '4')
        self.sdp.add_keyvalue('AEV', '5.5')
        self.sdp.add_keyvalue('AFV', 'abc')
        self.sdp.add_keyvalue('AGW', '4')
        self.sdp.add_keyvalue('AHW', '5 6 75')
        self.sdp.add_keyvalue('AIS', '?')
        self.sdp.add_keyvalue('AJV', '?')
        self.sdp.add_keyvalue('AKW', '?')
        self.sdp.add_keyvalue('iq', '?')
        self.sdp.add_keyvalue('TOV', '4000D3349FEBBEAE') # legacy
        self.sdp.add_keyvalue('ALF', '4000D3349FEBBEAE')
        datagram = self.sdp.encode(controllerid='def456')
        self.assertTrue(isinstance(datagram, str))
        self.assertEqual(sorted(datagram.splitlines()), [
            'AAS:1',
            'ABV:2',
            'ACV:3.5',
            'ADV:4',
            'AEV:5.5',
            'AFV:abc',
            'AGW:4',
            'AHW:5 6 75',
            'AIS:?',
            'AJV:?',
            'AKW:?',
            'ALF:4000D3349FEBBEAE',
            'TOV:4000D3349FEBBEAE',
            'id:def456',
            'ip:10.0.0.10',
            'iq:?',
        ])

    def test_encode_without_id(self):
        ''' Test encoder without id'''
        self.assertRaises(SDPException, self.sdp.encode)

    def test_decode_valid(self):
        ''' Test decoder with valid datagram '''
        self.sdp.decode( \
            'id:abc123\n' \
            'AAS:1\n' \
            'ABV:2\n' \
            'ACV:3.5\n' \
            'ADV:4\n' \
            'AEV:5.5\n' \
            'AFV:abc\n' \
            'AGW:4\n' \
            'AHW:5 6 75\n' \
            'AIS:?\n' \
            'AJV:?\n' \
            'AKW:?\n' \
            'iq:?\n' \
            'ip:10.0.0.10\n' \
            'ALF:4000D3349FEBBEAE\n' \
            'TOV:4000D3349FEBBEAE\n' \
            'AMW:8 null 9\n')

        d = self.sdp.get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')

        d = self.sdp.get_data('ip')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '10.0.0.10')

        d = self.sdp.get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 1)

        d = self.sdp.get_data('ABV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '2')

        d = self.sdp.get_data('ACV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '3.5')

        d = self.sdp.get_data('ADV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '4')

        d = self.sdp.get_data('AEV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '5.5')

        d = self.sdp.get_data('AFV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc')

        d = self.sdp.get_data('AGW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [4])

        d = self.sdp.get_data('AHW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [5, 6, 75])

        d = self.sdp.get_data('AMW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [8, None, 9])

        d = self.sdp.get_data('ALF')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '4000D3349FEBBEAE')

        d = self.sdp.get_data('TOV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '4000D3349FEBBEAE')

        d = self.sdp.get_data('AIS')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        d = self.sdp.get_data('AJV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        d = self.sdp.get_data('AKW')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        d = self.sdp.get_data('iq')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

    def test_decode_invalid(self):
        ''' Test decoder with invalid datagram '''
        self.assertRaises(SDPDecodeException, self.sdp.decode, '')
        self.assertRaises(SDPDecodeException, self.sdp.decode, '\n')
        self.assertRaises(SDPDecodeException, self.sdp.decode, \
            'id:abc\nABC')
        self.assertRaises(SDPDecodeException, self.sdp.decode, \
            'id:abc\nABS:abc')
        self.assertRaises(SDPDecodeException, self.sdp.decode, \
            'id:abc\nACW:123 bcd')
        self.assertRaises(SDPDecodeException, self.sdp.decode, \
            'id:abc\nADW:1.0 2.2')
        self.assertRaises(SDPDecodeException, self.sdp.decode, \
            'id:abc\nxyz:123 : 456')
        self.assertRaises(SDPDecodeException, self.sdp.decode, \
            'id:abc\nxyz:\n')
