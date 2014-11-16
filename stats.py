''' Statistics storage module
'''
import time

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'Stats',
]

class Stats(object):
    ''' Statistics storage '''
    def __init__(self):
        ''' Create statistics storage
        '''
        self._stats = {}
        self.set('created', time.time())

    def set(self, name, val):
        ''' Set stats element

        :param name: element name
        :param val: element value
        '''
        self._stats[name] = val

    def set_timestamp(self, name):
        ''' Set current timestamp to the element value

        :param name: element name
        '''
        self.set(name, time.time())

    def add(self, name, val):
        ''' Add number to element couter

        :param name: element name
        :param val: value to add to the existing element value
        '''
        if not name in self._stats:
            self.set(name, 0)
        self._stats[name] = self._stats[name] + val

    def get(self):
        ''' Get stats data

        :returns: stats data
        '''
        return self._stats

    def __str__(self):
        return(str(self._stats))
