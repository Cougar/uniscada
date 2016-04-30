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
        self._storage = None
        self._services = Services()

    def get_id(self):
        ''' Get id of servicegroup

        :returns: servicegroup id
        '''
        return self._id

    def set_storage(self, storage):
        """ Set storage

        :param storage: storage
        """
        self._storage = storage

    def _set_service(self, srvname, service):
        ''' Set service setup data

        :param srvname: service name
        :param service: service setup data
        '''
        log.info('_set_service(%s, %s, %s)', str(self._id), str(srvname), str(service))
        self.get_services().find_by_id(srvname).set_setup(service)

    def set_service(self, service):
        ''' Set service setup data and save to storage

        :param srvname: service name
        :param service: service setup data
        '''
        log.info('set_service(%s, %s)', str(self._id), str(service))
        srvname = service.get('sta_reg', None)
        if not srvname:
            log.error('sta_reg missing')
            return
        self._set_service(srvname, service)
        self.save_service(srvname, service)

    def save_service(self, srvname, service):
        ''' Save service data to storage

        :param service: service setup data
        '''
        log.info('save_service(%s, %s, %s)', str(self._id), str(srvname), str(service))
        self._storage.hset_data('servicegroup/' + self._id + '/services', srvname, service)

    def load_service(self, srvname):
        ''' Load service data from storage

        :param srvname: service name
        '''
        log.info('load_service(%s, %s)', str(self._id), str(srvname))
        service = self._storage.hget_data('servicegroup/' + self._id + '/services', srvname)
        if not service:
            log.error('no such service data in storage: %s', srvname)
            return
        self._set_service(srvname, service)

    def load_all_services(self):
        ''' Load all services from storage
        '''
        for srvname in self._storage.hkeys('servicegroup/' + self._id + '/services'):
            self.load_service(srvname)

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
        for service in self.get_services().get_id_list():
            r['services'].append(self.get_services().get_id(service).get_service_data_v1())
        return r

    def __str__(self):
        return(str(self._id) + ': ' +
               'services = ' + str(self.get_services()))
