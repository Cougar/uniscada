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
        self.host.receiver('message')
        receiver.assert_called_once_with(self.host, 'message')

    def test_missing_sender(self):
        self.host.send('message')

    def test_sender(self):
        sender = Mock()
        self.host.set_sender(sender)
        self.host.send('message')
        sender.assert_called_once_with(self.host, 'message')

    def test_remove_independent_instance(self):
        self.host.remove()

    def test_remove_list_instance(self):
        globallist = Mock()
        globallist.remove_by_id = Mock()
        self.host = Host(('1.2.3.4', 12345), globallist)
        self.host.remove()
        globallist.remove_by_id.assert_called_once_with(self.host.get_id())
