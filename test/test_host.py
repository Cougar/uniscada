import unittest
from mock import Mock

from host import Host

class HostTests(unittest.TestCase):
    '''
    This is the unittest for the uniscada.host module
    '''
    def setUp(self):
        self.host = Host(('1.2.3.4', 12345))

    def test_id(self):
        ''' Test host id '''
        self.assertEqual(self.host.get_id(), ('1.2.3.4', 12345))

    def test_missing_receiver(self):
        self.host.receiver('message')

    def test_receiver(self):
        receiver = Mock()
        self.host.set_receiver(receiver)
        self.host.receiver(b'message')
        receiver.assert_called_once_with(self.host, 'message')

    def test_missing_sender(self):
        self.host.send('message')

    def test_sender(self):
        sender = Mock()
        self.host.set_sender(sender)
        self.host.set_addr('addr')
        self.host.send('message')
        sender.assert_called_once_with(self.host, 'addr', b'message')

    def test_remove_independent_instance(self):
        self.host._remove()

    def test_remove_list_instance(self):
        globallist = Mock()
        globallist.remove_by_id = Mock()
        self.host = Host(('1.2.3.4', 12345), globallist)
        self.host._remove()
        globallist.remove_by_id.assert_called_once_with(self.host.get_id())

    def test_add_controller(self):
        controller = Mock()
        self.host.add_controller(controller)
        self.assertRaises(Exception, self.host.add_controller, controller)

    def test_del_controller(self):
        globallist = Mock()
        globallist.remove_by_id = Mock()
        self.host = Host(('1.2.3.4', 12345), globallist)
        controller = Mock()
        self.assertRaises(Exception, self.host.del_controller, controller)
        self.host.add_controller(controller)
        self.host.del_controller(controller)
        globallist.remove_by_id.assert_called_once_with(self.host.get_id())
