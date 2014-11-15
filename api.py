''' API call dispatcher
'''

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'API', 'get',
]

class API(object):
    ''' Call API endpoints '''
    def __init__(self, usersessions, controllers, servicegroups):
        self._usersessions = usersessions
        self._controllers = controllers
        self._servicegroups = servicegroups

    def get(self, user, resource, filter=None):
        ''' Return API call result

        :param user: username
        :param resource: resource (command)
        :param filter: optional filter

        :returns: resource
        '''
        log.debug('resource: %s, filter: %s', resource, str(filter))
        if resource == 'hosts':
            from api_hosts import API_hosts
            data = API_hosts(self._usersessions, self._controllers, self._servicegroups).output(user, filter)
        elif resource == 'controllers':
            from api_controllers import API_controllers
            data = API_controllers(self._usersessions, self._controllers, self._servicegroups).output(user, filter)
        elif resource == 'hostgroups':
            from api_hostgroups import API_hostgroups
            data = API_hostgroups(self._usersessions, self._controllers, self._servicegroups).output(user, filter)
        elif resource == 'servicegroups':
            from api_servicegroups import API_servicegroups
            data = API_servicegroups(self._usersessions, self._controllers, self._servicegroups).output(user, filter)
        elif resource == 'services':
            from api_services import API_services
            data = API_services(self._usersessions, self._controllers, self._servicegroups).output(user, filter)
        else:
            data = { 'message': 'unknown resource' }
        return data
