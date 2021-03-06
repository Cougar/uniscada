''' Keep track of list of objects identified by some id
'''

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'GlobalList', 'find_by_id', 'remove_by_id', 'get_id_list',
]

class GlobalList(object):
    ''' List of all members '''

    def __init__(self, storage=None, key=None):
        self._storage = storage
        self._storage_key = key
        self._members = {}
        self.class_name = self.getMemberClass()
        log.info('Initialise a new global list of %s', str(self.class_name))

    def getMemberClass(self):
        ''' Return a class name that should be used for members
        '''
        raise Exception("please implement getMemberClass() method")

    def find_by_id(self, id):
        ''' Return a list member or if there is no existing member
        with that id, then a new member instance will be created.

        :param id: id

        :returns: member instance
        '''
        log.debug('find_by_id(%s)', id)
        if not id in self._members:
            self._members[id] = self.class_name(id, listinstance=self)
            if self._storage:
                set_storage = getattr(self._members[id], 'set_storage', None)
                if set_storage:
                    set_storage(self._storage)
                if self._storage_key:
                    self._storage.sadd(self._storage_key, id)
            log.debug('find_by_id(%s): created a new member(%s)', str(id), str(self._members[id]))
        else:
            log.debug('find_by_id(%s): existing member(%s)', str(id), str(self._members[id]))
        return self._members[id]

    def get_id(self, id):
        if id in self._members:
            return self._members[id]
        else:
            return None

    def get_id_list(self):
        ''' Generates a list of member instances

        :returns: Generated instance for each member
        '''
        if not self._members:
            return
        for id in self._members.keys():
            yield(id)

    def remove_by_id(self, id):
        log.debug('remove_by_id(%s)', str(id))
        if id in self._members:
            del self._members[id]
            if self._storage and self._storage_key:
                self._storage.srem(self._storage_key, id)
        else:
            log.error("No such id: %s", str(id))

    def __getstate__(self):
        return self.__dict__

    def __str__(self):
        s = ''
        for id in self.get_id_list():
            s += '\n  ' + str(self.find_by_id(id))
        return(s)
