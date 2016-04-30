''' Keep track of all servicegroups
'''

from globallist import GlobalList
from servicegroup import ServiceGroup

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'ServiceGroups', 'getMemberClass',
]

class ServiceGroups(GlobalList):
    ''' List of all servicegroups '''

    def __init__(self, storage=None, key=None):
        super(ServiceGroups, self).__init__(storage=storage, key=key)

    def restore(self):
        if self._storage and self._storage_key:
            if self._storage.exists(self._storage_key):
                log.info('restore old data')
                tmp_key = self._storage_key + '__old'
                self._storage.rename(self._storage_key, tmp_key)
                for sgname in self._storage.sscan_iter(tmp_key):
                    servicegroup = self.find_by_id(sgname)
                    servicegroup.load_all_services()
        return self

    def getMemberClass(self):
        return ServiceGroup
