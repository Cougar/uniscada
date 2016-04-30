''' Keep track of all known controllers
'''

from globallist import GlobalList
from controller import Controller

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'Controllers', 'getMemberClass',
]

class Controllers(GlobalList):
    ''' List of all known controllers '''

    def __init__(self, storage=None, key=None, core=None):
        self._core = core
        super(Controllers, self).__init__(storage=storage, key=key)

    def restore(self):
        if self._storage and self._storage_key:
            if self._storage.exists(self._storage_key):
                log.info('restore old data')
                tmp_key = self._storage_key + '__old'
                self._storage.rename(self._storage_key, tmp_key)
                for controllerid in self._storage.sscan_iter(tmp_key):
                    controller = self.find_by_id(controllerid)
                    controller.set_servicegroups(self._core.servicegroups())
                    controller.set_msgbus(self._core.msgbus())
                self._storage.delete(tmp_key)
        return self

    def getMemberClass(self):
        return Controller
