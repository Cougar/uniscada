from apibase import APIBase
from sessionexception import SessionException

from schema import Schema

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class APIhostgroups(APIBase):

    API_PATH = APIBase.API_BASE_PATH + '/hostgroups/'

    _schema_GET = Schema(None)

    def _request_get(self, **kwargs):
        """ Return list of all hostgroups """
        log.debug('_request_get(%s)', str(kwargs))
        user = kwargs.get('user', None)
        userdata = self._usersessions.find_by_id(user).get_userdata()
        r = []
        if 'hostgroups' in userdata:
            for hostgroup in userdata['hostgroups']:
                r.append({'hostgroup': hostgroup, \
                    'alias': userdata['hostgroups'][hostgroup]. \
                        get('alias', '')})
        return {'status': 200, 'bodydata': r}

    def _request_get_with_filter(self, **kwargs):
        """ Return details of one hostgroup """
        log.debug('_request_get_with_filter(%s)', str(kwargs))
        user = kwargs.get('user', None)
        usersession = self._usersessions.find_by_id(user)
        userdata = usersession.get_userdata()
        r = []
        for hostgroup in kwargs.get('filter', '').split(','):
            if not 'hostgroups' in userdata:
                return {'status': 404}
            if not hostgroup in userdata['hostgroups']:
                raise SessionException('no such hostgroup for this user')
            hg = {}
            hg['hostgroup'] = hostgroup
            hg['hosts'] = []
            if 'members' in userdata['hostgroups'][hostgroup]:
                for host, alias in \
                        userdata['hostgroups'][hostgroup]['members'].items():
                    if usersession.check_access(host):
                        r1 = {'id': host, 'alias': alias}
                        h = self._controllers.get_id(host)
                        if h:
                            servicegroup = h.get_setup().get('servicetable', '')
                            r1['servicegroup'] = servicegroup
                        else:
                            log.warning('host "%s" with alias "%s" ' \
                                'doesnt exists but is in user "%s" ' \
                                'hostgroup "%s"', \
                                host, alias, user, hostgroup)
                        hg['hosts'].append(r1)
            r.append(hg)
        return {'status': 200, 'bodydata': r}
