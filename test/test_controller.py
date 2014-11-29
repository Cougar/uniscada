import unittest
import time

from controller import Controller

class ControllerTests(unittest.TestCase):
    '''
    This is the unittest for the uniscada.controller module
    '''
    def setUp(self):
        self.controller = Controller('123')

    def test_id(self):
        ''' Test controller id '''
        self.assertEqual(self.controller.get_id(), '123')

    def test_state_reg(self):
        ''' Test controller state register without timestamp '''
        timestamp = time.time()
        self.controller.set_state_reg('ABC', 123)
        (val, ts) = self.controller.get_state_reg('ABC')
        self.assertEqual(val, 123)
        self.assertAlmostEqual(ts, timestamp, delta=2)

    def test_state_reg(self):
        ''' Test controller state register with timestamp '''
        self.controller.set_state_reg('ABC', 123, ts=999)
        self.assertEqual(self.controller.get_state_reg('ABC'), (123, 999))

    def test_state_reg(self):
        ''' Test controller state missing register '''
        self.assertEqual(self.controller.get_state_reg('xxx'), (None, None))

    def test_state_register_list(self):
        ''' Test get_state_register_list() method '''
        self.assertEqual(list(self.controller.get_state_register_list()), [])
        self.controller.set_state_reg('ABC', 123, ts=100)
        self.controller.set_state_reg('DEF', 'abc', ts=200)
        self.controller.set_state_reg('GHI', [4, 5, 6], ts=300)
        self.assertListEqual(sorted(list(self.controller.get_state_register_list())), [('ABC', 123, 100), ('DEF', 'abc', 200), ('GHI', [4, 5, 6], 300)])
