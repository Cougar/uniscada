import unittest
import tornado.ioloop
from tornado.testing import AsyncTestCase, gen_test

from msgbus import MsgBus

class MsgBusTest(AsyncTestCase):
    '''
    This is the unittest for the uniscada.msgbus module
    '''
    def setUp(self):
        super(MsgBusTest, self).setUp()
        self.msgbus = MsgBus()

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    def test_send_unknown_subject(self):
        ''' Test message send when no listeners subscribed '''
        self.msgbus.publish('nosubject', 'message0')

    def test_subscription(self):
        ''' Test subscriptions with different tokens '''
        self.msg_subject1 = None
        self.msg_subject2 = None
        self.msg_token1 = None
        self.msg_token2 = None
        self.msg_message1 = None
        self.msg_message2 = None

        self.msgbus.subscribe('token1', 'subject1', 'owner', self._cb1)
        self.msgbus.subscribe('token2', 'subject1', 'owner', self._cb2)
        self.msgbus.subscribe('token1', 'subject2', 'owner', self._cb3)

        self.msgbus.publish('subject1', 'message1')
        self.io_loop.add_callback(self.stop)
        self.wait()

        self.assertEqual('subject1', self.msg_subject1)
        self.assertEqual('token1', self.msg_token1)
        self.assertEqual('message1', self.msg_message1)

        self.assertEqual('subject1', self.msg_subject2)
        self.assertEqual('token2', self.msg_token2)
        self.assertEqual('message1', self.msg_message2)


    def _cb1(self, token, subject, message):
        self.msg_subject1 = subject
        self.msg_token1 = token
        self.msg_message1 = message

    def _cb2(self, token, subject, message):
        self.msg_subject2 = subject
        self.msg_token2 = token
        self.msg_message2 = message

    def _cb3(self, token, subject, message):
        self.assertTrue(False)
