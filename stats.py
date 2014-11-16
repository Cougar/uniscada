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
        (ref, n) = self._get_ref(name)
        ref[n] = val

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
        (ref, n) = self._get_ref(name)
        ref[n] = ref[n] + val

    def get(self):
        ''' Get stats data

        :returns: stats data
        '''
        return self._stats

    def _get_ref(self, name):
        ref = self._stats
        names = name.split('/')
        parents = names[:-1]
        leaf = names[-1:][0]
        for n in parents:
            if not n in ref:
                ref[n] = {}
            elif not isinstance(ref[n], dict):
                raise Exception('cant change existing stats name "' + n + '" to subname for "' + name + '"')
            ref = ref[n]
        if not leaf in ref:
            ref[leaf] = 0
        elif isinstance(ref[leaf], dict):
            raise Exception('stats name "' + name + '" is a subname')
        return (ref, leaf)

    def __str__(self):
        return(str(self._stats))
