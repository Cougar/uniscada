""" API call dispatcher
"""

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

from api_hosts import APIhosts
from api_controllers import APIcontrollers
from api_hostgroups import APIhostgroups
from api_servicegroups import APIservicegroups
from api_services import APIservices
from api_usersessions import APIusersessions

class API(object):
    """ Call API endpoints """
    def __init__(self, core):
        self._core = core

    def get(self, **kwargs):
        """ Return API call result

        :param **kwargs: parameters

        :returns: resource
        """
        log.debug('get(%s)', str(kwargs))
        resource = kwargs.get('resource', None)
        if resource == 'hosts':
            return APIhosts(self._core).output(**kwargs)
        elif resource == 'controllers':
            return APIcontrollers(self._core).output(**kwargs)
        elif resource == 'hostgroups':
            return APIhostgroups(self._core).output(**kwargs)
        elif resource == 'servicegroups':
            return APIservicegroups(self._core).output(**kwargs)
        elif resource == 'services':
            return APIservices(self._core).output(**kwargs)
        elif resource == 'usersessions':
            return APIusersessions(self._core).output(**kwargs)
        else:
            return {'status': 501, \
                'message': 'unknown resource: %s' % \
                    str(kwargs.get('resource', None))}
