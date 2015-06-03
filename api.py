""" API call dispatcher
"""

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

from api_controllers import APIcontrollers
from api_hostgroups import APIhostgroups
from api_hosts import APIhosts
from api_servicegroups import APIservicegroups
from api_services import APIservices
from api_usersessions import APIusersessions

class API(object):
    """ Call API endpoints """

    RESOURCES = {
        'controllers': APIcontrollers,
        'hostgroups': APIhostgroups,
        'hosts': APIhosts,
        'servicegroups': APIservicegroups,
        'services': APIservices,
        'usersessions': APIusersessions
    }

    def __init__(self, core):
        self._core = core

    def get(self, **kwargs):
        """ Return API call result

        :param **kwargs: parameters

        :returns: resource
        """
        log.debug('get(%s)', str(kwargs))
        resource = kwargs.get('resource', None)
        if resource in self.RESOURCES:
            return self.RESOURCES[resource](self._core).output(**kwargs)
        else:
            return {'status': 501, \
                'message': 'unknown resource: %s' % \
                    str(kwargs.get('resource', None))}
