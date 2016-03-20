''' Message bus implementation
'''
import copy

from functools import partial
import tornado.ioloop

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'MsgBus',
    'subscribe', 'publish', 'unsubscribe_all',
]

class MsgBus(object):
    ''' Message bus '''
    def __init__(self,):
        self._subscriptions = {}

    def subscribe(self, token, subject, owner, func):
        ''' Subscribe a bus message listener

        :param token: token
        :param subject: message subject to listen
        :param owner: listener
        :param func: callback function func(token, subject, message)
        '''
        log.info('subscribe(%s, %s, %s, %s)', str(token), str(subject), str(owner), str(func))
        if not owner in self._subscriptions:
            self._subscriptions[owner] = {}
        if not token in self._subscriptions[owner]:
            self._subscriptions[owner][token] = {}
        self._subscriptions[owner][token][subject] = func

    def publish(self, subject, message):
        ''' Send messade to all subscribers

        :param subject: message subject
        :param message: message data
        '''
        log.debug('publish(%s, %s)', str(subject), str(message))
        for owner in self._subscriptions.keys():
            for token in self._subscriptions[owner].keys():
                if subject in self._subscriptions[owner][token]:
                    tornado.ioloop.IOLoop.instance().add_callback(partial(self._publish_one, token, subject, owner, self._subscriptions[owner][token][subject], copy.deepcopy(message)))

    def _publish_one(self, token, subject, owner, func, message):
        func(token, subject, message)

    def unsubscribe(self, token, subject, owner):
        ''' Unsubscribe a bus message listener

        All parameters must be the same that was used for subscribe

        :param token: token
        :param subject: message subject to listen
        :param owner: listener
        '''
        log.info('unsubscribe(%s, %s, %s)', str(token), str(subject), str(owner))
        if not owner in self._subscriptions:
            raise Exception('no subscriptions for this owner')
        if not token in self._subscriptions[owner]:
            raise Exception('unknown token')
        if not subject in self._subscriptions[owner][token]:
            raise Exception('no subscription')
        del self._subscriptions[owner][token][subject]
        if not len(self._subscriptions[owner][token]):
            del self._subscriptions[owner][token]
        if not len(self._subscriptions[owner]):
            del self._subscriptions[owner]

    def unsubscribe_all(self, owner):
        ''' Unsubscribe all listeners of one owner

        :param owner: listener
        '''
        log.info('unsubscribe_all(%s)', str(owner))
        if owner in self._subscriptions:
            del self._subscriptions[owner]

    def gen_get_subscriptions(self, owner):
        ''' Generate list of subscriptions

        :param owner: listener

        :yields: Generated (token, subject) pair for each subscription
        '''
        if owner in self._subscriptions:
            for token in self._subscriptions[owner].keys():
                for subject in self._subscriptions[owner][token]:
                    yield (token, subject)

    def __str__(self):
        s = 'Subscriptions:'
        for owner in self._subscriptions.keys():
            s += '  ' + str(owner) + ':\n'
            for token in self._subscriptions[owner].keys():
                s+= '    token=' + str(token) + ', subscriptions=' + ','.join(self._subscriptions[owner][token].keys()) + '\n'
        return s
