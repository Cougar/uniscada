from apibase import APIBase
from sessionexception import SessionException

from schema import Schema

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class APIhosts(APIBase):

    API_PATH = APIBase.API_BASE_PATH + '/hosts/'

    _schema_GET = Schema(None)

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
            if  usersession.check_scope('stats:host'):
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
        usersession = self._usersessions.find_by_id(user)
        r = []
        for host in kwargs.get('filter', '').split(','):
            if not usersession.check_access(host):
                raise SessionException('unknown host')
            h = self._controllers.get_id(host)
            if not h:
                raise SessionException('unknown host')
            r.append(h.get_host_data_v1(usersession.check_scope))
        return {'status': 200, 'bodydata': r}
