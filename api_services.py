from apibase import APIBase
from sessionexception import SessionException

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class APIservices(APIBase):
    def _request_get(self, **kwargs):
        """ Process 'GET' request """
        raise SessionException('missing parameter')

    def _request_get_with_filter(self, **kwargs):
        """ Return details of one controller services """
        log.debug('_request_get_with_filter(%s)', str(kwargs))
        user = kwargs.get('user', None)
        controller = kwargs.get('filter', None)
        usersession = self._usersessions.find_by_id(user)
        if not usersession.check_access(controller):
            raise SessionException('unknown controller')
        c = self._controllers.get_id(controller)
        if not c:
            return {'status': 404}
        servicegroup = None
        setup = c.get_setup()
        if setup:
            servicetable = setup.get('servicetable', None)
            if servicetable:
                servicegroup = self._servicegroups.get_id(servicetable)
        return {'status': 200, \
            'bodydata': c.get_service_data_v1(servicegroup)}
