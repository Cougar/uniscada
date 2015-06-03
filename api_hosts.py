from apibase import APIBase
from sessionexception import SessionException

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class APIhosts(APIBase):

    API_PATH = APIBase.API_BASE_PATH + '/hosts/'

    def _request_get(self, **kwargs):
        """ Return list of all hosts """
        log.debug('_request_get(%s)', str(kwargs))
        user = kwargs.get('user', None)
        usersession = self._usersessions.find_by_id(user)
        r = []
        for h in self._hosts.get_id_list():
            host = self._hosts.find_by_id(h)
            entry = []
            for controller in host.get_controller_list():
                c = controller.get_id()
                if usersession.check_access(c):
                    entry.append(c)
            if  usersession.is_admin():
                r.append({
                    'host': h,
                    'controllers': entry,
                    'stats': host.get_stats()
                })
            elif len(entry):
                r.append({'host': h, 'controllers': entry})
        return {'status': 200, 'bodydata': r}

    def _request_get_with_filter(self, **kwargs):
        """ Return details of one host """
        log.debug('_request_get_with_filter(%s)', str(kwargs))
        user = kwargs.get('user', None)
        host = kwargs.get('filter', None)
        usersession = self._usersessions.find_by_id(user)
        if not usersession.check_access(host):
            raise SessionException('unknown host')
        h = self._controllers.get_id(host)
        if h:
            return {'status': 200, \
                'bodydata': h.get_host_data_v1(usersession.is_admin())}
        return {'status': 404}
