''' Servicegroup data structure
'''
import time

from services import Services

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'ServiceGroup',
    'get_id', 'get_services',
    'get_servicegroup_data_v1',
]

class ServiceGroup(object):
    ''' One servicegroup '''
    def __init__(self, id, listinstance = None):
        ''' Create new servicegroup instance

        :param id: servicegroup id (name)
        :param listinstance: optional ServiceGroups instance
        '''
        log.info('Create a new servicegroup (%s)', str(id))
        self._id = id
        self._services = Services()

    def get_id(self):
        ''' Get id of servicegroup

        :returns: servicegroup id
        '''
        return self._id

    def get_services(self):
        ''' Get Services instance

        :returns: Services instance
        '''
        return self._services

    def get_servicegroup_data_v1(self):
        ''' Return servicegroup data in API v1 format

        :returns: servicegroup data in API v1 format
        '''
        r = {}
        r['servicegroup'] = self._id
        r['services'] = []
        for service in self._services.get_id_list():
            r['services'].append(self._services.get_id(service).get_service_data_v1())
        return r

    def __str__(self):
        return(str(self._id) + ': ' +
               'services = ' + str(self._services))
