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
        self.sdp += ('AAS', 2)
        d = self.sdp.get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 2)
        self.assertEqual(self.sdp.get_data('AAs'), None)
        self.assertEqual(self.sdp.get_data('aaS'), None)

        self.sdp.remove_data('AAS')
        self.assertIsNone(self.sdp.get_data('AAS'))
        with self.assertRaises(SDPException):
            self.sdp.remove_data('AAS')

        self.sdp += ('ABS', '3')
        d = self.sdp.get_data('ABS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 3)

        self.sdp.remove_data('ABS')
        self.assertIsNone(self.sdp.get_data('ABS'))
        with self.assertRaises(SDPException):
            self.sdp.remove_data('ABS')

        with self.assertRaises(SDPException):
            self.sdp += ('AxS', -1)
        with self.assertRaises(SDPException):
            self.sdp += ('AyS', 4)
        with self.assertRaises(SDPException):
            self.sdp += ('AqS', '4')
        with self.assertRaises(SDPException):
            self.sdp += ('AXS', 'a')
        with self.assertRaises(SDPException):
            self.sdp += ('AYS', [1, 2])
        with self.assertRaises(SDPException):
            self.sdp += ('AZS', None)

    def test_add_status(self):
        ''' Test setting/getting Status key:val '''
        self.sdp.add_status('AA', 2)
        d = self.sdp.get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 2)
        self.assertEqual(self.sdp.get_data('AAs'), None)
        self.assertEqual(self.sdp.get_data('aaS'), None)

        self.sdp.remove_data('AAS')
        self.assertIsNone(self.sdp.get_data('AAS'))
        with self.assertRaises(SDPException):
            self.sdp.remove_data('AAS')

        with self.assertRaises(SDPException):
            self.sdp.add_status('AX', 'a')
        with self.assertRaises(SDPException):
            self.sdp.add_status('AY', [1, 2])
        with self.assertRaises(SDPException):
            self.sdp.add_status('AZ', None)

    def test_add_keyvalue_value(self):
        ''' Test setting/getting key:val for Value '''
        self.sdp += ('AAV', 1234)
        d = self.sdp.get_data('AAV')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 1234)
        self.assertEqual(self.sdp.get_data('AAv'), None)
        self.assertEqual(self.sdp.get_data('aaV'), None)

        self.sdp.remove_data('AAV')
        self.assertIsNone(self.sdp.get_data('AAV'))
        with self.assertRaises(SDPException):
            self.sdp.remove_data('AAV')

        self.sdp += ('ABV', 1.5)
        d = self.sdp.get_data('ABV')
        self.assertTrue(isinstance(d, float))
        self.assertEqual(d, 1.5)

        self.sdp += ('ACV', 'abc')
        d = self.sdp.get_data('ACV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc')

        self.sdp += ('ADV', 'cde xyz')
        d = self.sdp.get_data('ADV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'cde xyz')

        self.sdp += ('AEV', '1 2 3.5')
        d = self.sdp.get_data('AEV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '1 2 3.5')

        self.sdp += ('AFV', 'not null string')
        d = self.sdp.get_data('AFV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'not null string')

        self.sdp += ('AGV', 'null')
        self.assertEqual(self.sdp.get_data('AGV'), 'null')

        self.sdp += ('AHV', '')
        self.assertEqual(self.sdp.get_data('AHV'), '')

        with self.assertRaises(SDPException):
            self.sdp += ('AXV', [1, 2])

    def test_add_keyvalue_values_list(self):
        ''' Test setting/getting key:val for List of Values (list) '''
        self.sdp += ('AAW', [1])
        d = self.sdp.get_data('AAW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1])
        self.assertEqual(self.sdp.get_data('AAw'), None)
        self.assertEqual(self.sdp.get_data('aaW'), None)

        self.sdp.remove_data('AAW')
        self.assertIsNone(self.sdp.get_data('AAW'))
        with self.assertRaises(SDPException):
            self.sdp.remove_data('AAW')

        self.sdp += ('ABW', [1, None, 2])
        d = self.sdp.get_data('ABW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1, None, 2])

        with self.assertRaises(SDPException):
            self.sdp += (\
            'AXV', [0, None, 3.5])

    def test_add_keyvalue_values(self):
        ''' Test setting/getting key:val for List of Values '''
        self.sdp += ('AAW', '1')
        d = self.sdp.get_data('AAW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1])
        self.assertEqual(self.sdp.get_data('AAw'), None)
        self.assertEqual(self.sdp.get_data('aaW'), None)

        self.sdp += ('ABW', '1 2 35')
        d = self.sdp.get_data('ABW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1, 2, 35])

        self.sdp += ('ACW', '0 null 35')
        d = self.sdp.get_data('ACW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [0, None, 35])

        with self.assertRaises(SDPException):
            self.sdp += ('AXW', 1)
        with self.assertRaises(SDPException):
            self.sdp += ('AYW', 1.5)
        with self.assertRaises(SDPException):
            self.sdp += ('AZW', 'a')
        with self.assertRaises(SDPException):
            self.sdp += ('AQW', '')
        with self.assertRaises(SDPException):
            self.sdp += ('AWW', None)
        with self.assertRaises(SDPException):
            self.sdp += ('AVW', [1.5])

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

        self.sdp.remove_data('AAV')
        self.assertIsNone(self.sdp.get_data('AAV'))
        with self.assertRaises(SDPException):
            self.sdp.remove_data('AAV')

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

    def test_add_keyvalue_float(self):
        ''' Test setting/getting Float key:val '''
        self.sdp += ('TOV', '4000D3349FEBBEAE')
        d = self.sdp.get_data('TOV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '4000D3349FEBBEAE')
        self.assertEqual(self.sdp.get_data('Tov'), None)
        self.assertEqual(self.sdp.get_data('T'), None)
        self.assertEqual(self.sdp.get_data('tov'), None)

        self.sdp.remove_data('TOV')
        self.assertIsNone(self.sdp.get_data('TOV'))
        with self.assertRaises(SDPException):
            self.sdp.remove_data('TOV')

        self.sdp += ('ALF', '4000D3349FEBBEAE')
        d = self.sdp.get_data('ALF')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '4000D3349FEBBEAE')
        self.assertEqual(self.sdp.get_data('Tov'), None)
        self.assertEqual(self.sdp.get_data('T'), None)
        self.assertEqual(self.sdp.get_data('tov'), None)

        self.sdp.remove_data('ALF')
        self.assertIsNone(self.sdp.get_data('ALF'))
        with self.assertRaises(SDPException):
            self.sdp.remove_data('ALF')

        with self.assertRaises(SDPException):
            self.sdp += ('ALF', 1)
        with self.assertRaises(SDPException):
            self.sdp += ('ALF', 1.5)
        with self.assertRaises(SDPException):
            self.sdp += ('ALF', [1, 2])

    def test_add_keyvalue_data(self):
        ''' Test setting/getting key:val for Other Data '''
        self.sdp += ('aa', '123')
        d = self.sdp.get_data('aa')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '123')
        self.assertEqual(self.sdp.get_data('AA'), None)
        self.assertEqual(self.sdp.get_data('a'), None)
        self.assertEqual(self.sdp.get_data('aaa'), None)

        self.sdp.remove_data('aa')
        self.assertIsNone(self.sdp.get_data('aa'))
        with self.assertRaises(SDPException):
            self.sdp.remove_data('aa')

        self.sdp += ('ab', 'null')
        d = self.sdp.get_data('ab')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'null')

        with self.assertRaises(SDPException):
            self.sdp += ('ax', 1)
        with self.assertRaises(SDPException):
            self.sdp += ('ay', 1.5)
        with self.assertRaises(SDPException):
            self.sdp += ('az', [1, 2])

    def test_add_keyvalue_illegal_data(self):
        ''' Test setting illegal key:val '''
        with self.assertRaises(SDPException):
            self.sdp += ('sha256', 1)

    def test_add_keyvalue_request_data(self):
        ''' Test setting/getting key:val where val == '?' '''
        self.sdp += ('AAS', '?')
        d = self.sdp.get_data('AAS')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        self.sdp += ('ABV', '?')
        d = self.sdp.get_data('ABV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        self.sdp += ('ACW', '?')
        d = self.sdp.get_data('ACW')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

    def test_timestamp(self):
        ''' Test get_timestamp() method '''
        self.assertEqual(self.sdp.get_timestamp(), None)
        self.sdp += ('in', '1')
        self.assertEqual(self.sdp.get_timestamp(), None)
        self.sdp += ('in', '2,123')
        self.assertEqual(self.sdp.get_timestamp(), 123)
        self.sdp += ('in', '3,456.7')
        self.assertEqual(self.sdp.get_timestamp(), 456.7)
        self.sdp += ('in', '4,567,89')
        self.assertEqual(self.sdp.get_timestamp(), None)
        self.sdp += ('in', '5,67.8.9')
        self.assertEqual(self.sdp.get_timestamp(), None)

    def test_seq(self):
        ''' Test get_in_seq() method '''
        self.assertEqual(self.sdp.get_in_seq(), None)
        self.sdp += ('in', '1')
        self.assertEqual(self.sdp.get_in_seq(), 1)
        self.sdp += ('in', '2,123')
        self.assertEqual(self.sdp.get_in_seq(), 2)
        self.sdp += ('in', '3,456.7')
        self.assertEqual(self.sdp.get_in_seq(), 3)
        self.sdp += ('in', '4,567,89')
        self.assertEqual(self.sdp.get_in_seq(), None)
        self.sdp += ('in', '5,67.8.9')
        self.assertEqual(self.sdp.get_in_seq(), None)

    def test_encode_with_id(self):
        ''' Test encoder for full packet'''
        self.sdp += ('id', 'abc123')
        self.sdp += ('ip', '10.0.0.10')
        self.sdp += ('AAS', 1)
        self.sdp += ('ABV', 2)
        self.sdp += ('ACV', 3.5)
        self.sdp += ('ADV', '4')
        self.sdp += ('AEV', '5.5')
        self.sdp += ('AFV', 'abc')
        self.sdp += ('AGW', '4')
        self.sdp += ('AHW', '5 6 75')
        self.sdp += ('AIS', '?')
        self.sdp += ('AJV', '?')
        self.sdp += ('AKW', '?')
        self.sdp += ('iq', '?')
        self.sdp += ('TOV', '4000D3349FEBBEAE') # legacy
        self.sdp += ('ALF', '4000D3349FEBBEAE')
        self.sdp += ('AMW', '8 null 9')
        self.sdp += ('ANV', '')
        self.sdp += ('ix', '')
        self.sdp += ('in', '1')
        datagram = self.sdp.encode()
        self.assertTrue(isinstance(datagram, str))
        self.assertEqual(datagram.splitlines()[0], 'id:abc123')
        self.assertEqual(datagram.splitlines()[1], 'in:1')
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
            'ANV:',
            'TOV:4000D3349FEBBEAE',
            'id:abc123',
            'in:1',
            'ip:10.0.0.10',
            'iq:?',
            'ix:',
        ])
        self.assertFalse(self.sdp.is_signed())
        self.assertFalse(self.sdp.check_signature())

    def test_encode_with_id_param(self):
        ''' Test encoder with id for full packet'''
        self.sdp += ('id', 'abc123')
        self.sdp += ('ip', '10.0.0.10')
        self.sdp += ('AAS', 1)
        self.sdp += ('ABV', 2)
        self.sdp += ('ACV', 3.5)
        self.sdp += ('ADV', '4')
        self.sdp += ('AEV', '5.5')
        self.sdp += ('AFV', 'abc')
        self.sdp += ('AGW', '4')
        self.sdp += ('AHW', '5 6 75')
        self.sdp += ('AIS', '?')
        self.sdp += ('AJV', '?')
        self.sdp += ('AKW', '?')
        self.sdp += ('iq', '?')
        self.sdp += ('TOV', '4000D3349FEBBEAE') # legacy
        self.sdp += ('ALF', '4000D3349FEBBEAE')
        self.sdp += ('ANV', '')
        self.sdp += ('ix', '')
        self.sdp += ('in', '1')
        datagram = self.sdp.encode(controllerid='def456')
        self.assertTrue(isinstance(datagram, str))
        self.assertEqual(datagram.splitlines()[0], 'id:def456')
        self.assertEqual(datagram.splitlines()[1], 'in:1')
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
            'ANV:',
            'TOV:4000D3349FEBBEAE',
            'id:def456',
            'in:1',
            'ip:10.0.0.10',
            'iq:?',
            'ix:',
        ])
        self.assertFalse(self.sdp.is_signed())
        self.assertFalse(self.sdp.check_signature())

    def test_encode_without_id(self):
        ''' Test encoder without id'''
        with self.assertRaises(SDPException):
            self.sdp.encode()

    def test_decode_valid(self):
        ''' Test decoder with valid datagram '''
        datagram = \
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
            'AMW:8 null 9\n' \
            'ANV:\n' \
            'ix:\n'

        sdp = SDP.decode(datagram)

        d = sdp.get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')

        d = sdp.get_data('ip')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '10.0.0.10')

        d = sdp.get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 1)

        d = sdp.get_data('ABV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '2')

        d = sdp.get_data('ACV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '3.5')

        d = sdp.get_data('ADV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '4')

        d = sdp.get_data('AEV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '5.5')

        d = sdp.get_data('AFV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc')

        d = sdp.get_data('AGW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [4])

        d = sdp.get_data('AHW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [5, 6, 75])

        d = sdp.get_data('AMW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [8, None, 9])

        d = sdp.get_data('ALF')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '4000D3349FEBBEAE')

        d = sdp.get_data('TOV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '4000D3349FEBBEAE')

        d = sdp.get_data('AIS')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        d = sdp.get_data('AJV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        d = sdp.get_data('AKW')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        d = sdp.get_data('ANV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '')

        d = sdp.get_data('iq')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        d = sdp.get_data('ix')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '')

        self.assertFalse(sdp.is_signed())
        self.assertFalse(sdp.check_signature())

    def test_decode_invalid(self):
        ''' Test decoder with invalid datagram '''
        with self.assertRaises(SDPDecodeException):
            SDP.decode('')
        with self.assertRaises(SDPDecodeException):
            SDP.decode('\n')
        with self.assertRaises(SDPDecodeException):
            SDP.decode('id:abc\nABC')
        with self.assertRaises(SDPDecodeException):
            SDP.decode('id:abc\nABS:abc')
        with self.assertRaises(SDPDecodeException):
            SDP.decode('id:abc\nACW:123 bcd')
        with self.assertRaises(SDPDecodeException):
            SDP.decode('id:abc\nADW:1.0 2.2')
        with self.assertRaises(SDPDecodeException):
            SDP.decode('id:abc\nxyz:123 : 456')
        with self.assertRaises(SDPDecodeException):
            SDP.decode('id:abc\nABS:\n')
        with self.assertRaises(SDPDecodeException):
            SDP.decode('id:abc\nABF:\n')
        with self.assertRaises(SDPDecodeException):
            SDP.decode('id:abc\nABW:\n')
        with self.assertRaises(SDPDecodeException):
            SDP.decode('id:abc\nAAS:1\nAAS:2\n')
        with self.assertRaises(SDPDecodeException):
            SDP.decode('id:abc\nAAS:1\nid:def\n')

    def test_encode_with_signature(self):
        ''' Test encoder for full packet with SHA1 HMAC signature'''
        self.sdp += ('id', 'abc123')
        self.sdp.set_secret_key('my-secret-key')
        self.sdp.set_nonce('12345')
        self.assertFalse(self.sdp.is_signed())
        datagram = self.sdp.encode()
        self.assertTrue(self.sdp.is_signed())
        self.assertTrue(isinstance(datagram, str))
        self.assertEqual(sorted(datagram.splitlines()), [
            'id:abc123',
            'sha256:Z/91VAs43GlbSHZVIzaqXSLKpunjLYPQfnhpHEvzYys=',
        ])

    def test_encode_with_signature2(self):
        ''' Test encoder for full packet with SHA1 HMAC signature'''
        self.sdp = SDP(secret_key='my-secret-key', nonce='12345')
        self.sdp += ('id', 'abc123')
        self.assertFalse(self.sdp.is_signed())
        datagram = self.sdp.encode()
        self.assertTrue(self.sdp.is_signed())
        self.assertTrue(isinstance(datagram, str))
        self.assertEqual(sorted(datagram.splitlines()), [
            'id:abc123',
            'sha256:Z/91VAs43GlbSHZVIzaqXSLKpunjLYPQfnhpHEvzYys=',
        ])

    def test_decode_with_valid_signature(self):
        ''' Test decoder with valid SHA1 HMAC signature '''
        datagram = 'id:abc123\n'
        signature = 'sha256:Z/91VAs43GlbSHZVIzaqXSLKpunjLYPQfnhpHEvzYys=\n'
        sdp = SDP.decode(datagram + signature, 'my-secret-key', '12345')

        self.assertTrue(sdp.is_signed())

        d = sdp.get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')

        self.assertTrue(sdp.check_signature())

    def test_decode_with_invalid_signature1(self):
        ''' Test decoder with invalid SHA1 HMAC signature (1) '''
        datagram = 'id:abc123\n'
        signature = 'sha256:wWYN9u1zKY+zqo0Z0xHxDL38tYsJBv+Mk5UAvN7hr5k=\n'
        with self.assertRaises(SDPDecodeException):
            SDP.decode(datagram + signature, 'wrong-secret-key', '12345')

    def test_decode_with_invalid_signature2(self):
        ''' Test decoder with invalid SHA1 HMAC signature (2)'''
        datagram = 'id:abc123\n'
        signature = 'sha256:wWYN9u1zKY+zqo0Z0xHxDL38tYsJBv+Mk5UAvN7hr5k=\n'
        with self.assertRaises(SDPDecodeException):
            SDP.decode(datagram + signature, 'my-secret-key', '54321')

    def test_decode_invalid_packet_with_valid_signature(self):
        ''' Test decoder with valid SHA1 HMAC signature '''
        with self.assertRaises(SDPException):
            SDP.decode(\
            'id:abc123\n' \
            'sha256:wWYN9u1zKY+zqo0Z0xHxDL38tYsJBv+Mk5UAvN7hr5k=\n' \
            'zx:123\n')

    def test_multipart_in_multipart_errors(self):
        ''' Test multipart SDP in another multipart SDP'''
        sdp1 = SDP()
        sdp1 += ('AAS', 1)
        sdp1 += ('in', '1,1440871960')

        sdp2 = SDP()
        sdp2 += ('in', '1,1440871960')
        ''' timestamp is not allowed in parent SDP '''
        with self.assertRaises(SDPException):
            sdp2 += sdp1

        sdp3 = SDP()
        sdp3 += ('AAS', 1)
        ''' other keys than "id" is not allowed in parent SDP '''
        with self.assertRaises(SDPException):
            sdp3 += sdp1

        sdp1 += ('id', 'abc123')
        ''' "id" in multipart but not in parent SDP '''
        with self.assertRaises(SDPException):
            self.sdp += sdp1
        self.sdp += ('id', 'abc123')
        self.sdp += sdp1
        ''' parent SDP "id" is different '''
        with self.assertRaises(SDPException):
            sdp1 += ('id', 'xyz789')
        sdp1 += ('id', 'abc123')
        ''' only "id" can be added to multipart parent '''
        with self.assertRaises(SDPException):
            self.sdp += ('in', '1,1440871960')

        sdp4 = SDP()
        ''' multipart SDP cant be added to another SDP '''
        with self.assertRaises(SDPException):
            sdp4 += self.sdp
        ''' SDP is already part of another multipart SDP '''
        with self.assertRaises(SDPException):
            sdp4 += sdp1
        ''' cant add SDP to itself '''
        with self.assertRaises(SDPException):
            sdp4 += sdp4

    def test_multipart_key_location_errors(self):
        ''' Test multipart SDP allowed keys in parent'''
        sdp1 = SDP()
        sdp1 += ('AAS', 1)
        sdp1 += ('in', '1,1440871960')

        self.sdp += sdp1
        self.sdp += ('id', 'abc123')
        with self.assertRaises(SDPException):
            self.sdp += ('AAS', 1)

    def test_multipart_id(self):
        ''' Test multipart SDP "id" logic'''
        self.assertIsNone(self.sdp.data['id'])
        self.sdp += ('id', 'abc123')
        d = self.sdp.get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')
        self.assertEqual(self.sdp.data['id'], 'abc123')

        sdp1 = SDP()
        sdp1 += ('AAS', 1)
        sdp1 += ('in', '1,1440871960')
        self.assertIsNone(sdp1.data['id'])
        sdp1 += ('id', 'abc123')
        d = sdp1.get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')
        self.assertEqual(sdp1.data['id'], 'abc123')

        self.sdp += sdp1

        ''' "id" comes from parent '''
        d = sdp1.get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')
        self.assertEqual(sdp1._multipart_parent.get_data('id'), 'abc123')
        self.assertIsNone(sdp1.data['id'])

    def test_multipart_add_remove(self):
        ''' Test multipart SDP assembly/disassembly '''
        sdp1 = SDP()
        sdp1 += ('AAS', 1)
        sdp1 += ('in', '1,1440871960')
        sdp2 = SDP()
        sdp2 += ('AAS', 2)
        sdp2 += ('in', '2,1440871961')

        self.sdp += ('id', 'abc123')

        with self.assertRaises(ValueError):
            self.sdp.remove_sdp_multipart(sdp1)
        with self.assertRaises(ValueError):
            self.sdp.remove_sdp_multipart(sdp2)
        self.assertListEqual(list(self.sdp.gen_get()), [self.sdp])

        self.sdp += sdp1
        self.assertListEqual(list(self.sdp.gen_get()), [sdp1])
        self.sdp += sdp2
        self.assertListEqual(list(self.sdp.gen_get()), [sdp1, sdp2])

        self.sdp.remove_sdp_multipart(sdp1)
        self.assertListEqual(list(self.sdp.gen_get()), [sdp2])
        self.sdp.remove_sdp_multipart(sdp2)
        self.assertListEqual(list(self.sdp.gen_get()), [self.sdp])

        with self.assertRaises(ValueError):
            self.sdp.remove_sdp_multipart(sdp1)
        with self.assertRaises(ValueError):
            self.sdp.remove_sdp_multipart(sdp2)

    def test_multipart(self):
        ''' Test multiple SDP packest in one datagram '''
        sdp1 = SDP()
        sdp1 += ('AAS', 1)
        sdp1 += ('in', '1,1440871960')
        sdp2 = SDP()
        sdp2 += ('AAS', 2)
        sdp2 += ('in', '2,1440871961')

        self.sdp += ('id', 'abc123')
        self.sdp += sdp1
        self.sdp += sdp2

        datagram = self.sdp.encode()
        self.assertTrue(isinstance(datagram, str))
        self.assertEqual(datagram.splitlines(), [
            'id:abc123',
            'in:1,1440871960',
            'AAS:1',
            'in:2,1440871961',
            'AAS:2',
        ])

    def test_multipart_decode(self):
        ''' Decode multipart SDP datagram '''
        datagram = \
            'id:abc123\n' \
            'in:1,1440871960\n' \
            'AAS:1\n' \
            'in:2,1440871961\n' \
            'AAS:2\n'
        self.sdp = SDP.decode(datagram)
        parts = list(self.sdp.gen_get())
        # part 1
        self.assertEqual(parts[0].get_in_seq(), 1)
        d = parts[0].get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')
        d = parts[0].get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 1)
        # part 2
        self.assertEqual(parts[1].get_in_seq(), 2)
        d = parts[1].get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')
        d = parts[1].get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 2)

    def test_multipart_decode_signed(self):
        ''' Decode multipart SDP datagram with signature '''
        datagram = \
            'id:abc123\n' \
            'in:1,1440871960\n' \
            'AAS:1\n' \
            'in:2,1440871961\n' \
            'AAS:2\n' \
            'sha256:wWYN9u1zKY+zqo0Z0xHxDL38tYsJBv+Mk5UAvN7hr5k=\n'
        self.sdp = SDP.decode(datagram)
        parts = list(self.sdp.gen_get())
        # part 1
        self.assertEqual(parts[0].get_in_seq(), 1)
        d = parts[0].get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')
        d = parts[0].get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 1)
        # part 2
        self.assertEqual(parts[1].get_in_seq(), 2)
        d = parts[1].get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')
        d = parts[1].get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 2)

    def test_multipart_decode_ack(self):
        ''' Decode multipart SDP ACK datagram '''
        datagram = \
            'id:abc123\n' \
            'in:1,1440871960\n' \
            'in:2,1440871961\n'
        self.sdp = SDP.decode(datagram)
        parts = list(self.sdp.gen_get())
        # part 1
        self.assertEqual(parts[0].get_in_seq(), 1)
        d = parts[0].get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')
        # part 2
        self.assertEqual(parts[1].get_in_seq(), 2)
        d = parts[1].get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')

    def test_multipart_same_timestamp(self):
        ''' Timestamp is not growing '''
        datagram = \
            'id:abc123\n' \
            'in:1,1440871960\n' \
            'AAS:1\n' \
            'in:2,1440871960\n' \
            'AAS:2\n'
        self.sdp = SDP.decode(datagram)
        parts = list(self.sdp.gen_get())
        # part 1
        self.assertEqual(parts[0].get_in_seq(), 1)
        d = parts[0].get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')
        d = parts[0].get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 1)
        # part 2
        self.assertEqual(parts[1].get_in_seq(), 2)
        d = parts[1].get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')
        d = parts[1].get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 2)

    def test_multipart_invalid2(self):
        ''' Timestamp is in wrong position '''
        datagram = \
            'id:abc123\n' \
            'AAS:1\n' \
            'in:1,1440871960\n' \
            'in:2,1440871961\n' \
            'AAS:2\n'
        return # FIXME
        with self.assertRaises(SDPDecodeException):
            self.sdp.decode(datagram)

    def test_multipart_invalid3(self):
        ''' No "id" field '''
        datagram = \
            'in:1,1440871960\n' \
            'AAS:1\n' \
            'in:2,1440871961\n' \
            'AAS:2\n'
        with self.assertRaises(SDPDecodeException):
            self.sdp.decode(datagram)

    def test_multipart_invalid4(self):
        ''' data before first "in" field '''
        datagram = \
            'AAA:1\n' \
            'id:abc123\n' \
            'in:1,1440871960\n' \
            'AAS:2\n' \
            'in:2,1440871961\n' \
            'AAS:3\n'
        return # FIXME
        with self.assertRaises(SDPDecodeException):
            self.sdp.decode(datagram)
