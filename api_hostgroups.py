from sessionexception import SessionException

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class API_hostgroups(object):
    def __init__(self, core):
        self._core = core
        self._usersessions = self._core.usersessions()
        self._controllers = self._core.controllers()
        self._servicegroups = self._core.servicegroups()

    def output(self, **kwargs):
        if kwargs.get('method', None) == 'GET':
            if kwargs.get('filter', None):
                return self._output_one_hostgroup(kwargs.get('user', None), kwargs.get('filter', None))
            else:
                return self._output_all_hostgroups(kwargs.get('user', None))
        else:
            return({ 'status': 405 })

    def _output_all_hostgroups(self, user):
        userdata = self._usersessions.find_by_id(user).get_userdata()
        r = []
        if 'hostgroups' in userdata:
            for hostgroup in userdata['hostgroups']:
                r.append({ 'hostgroup': hostgroup, 'alias': userdata['hostgroups'][hostgroup].get('alias', '') })
        return({ 'status': 200, 'bodydata': r })

    def _output_one_hostgroup(self, user, hostgroup):
        usersession = self._usersessions.find_by_id(user)
        userdata = usersession.get_userdata()
        if not 'hostgroups' in userdata:
            return({ 'status': 404 })
        if not hostgroup in userdata['hostgroups']:
            raise SessionException('no such hostgroup for this user')
        r = {}
        r['hostgroup'] = hostgroup
        r['hosts'] = []
        if 'members' in userdata['hostgroups'][hostgroup]:
            for host, alias in userdata['hostgroups'][hostgroup]['members'].items():
                if usersession.check_access(host):
                    r1 = { 'id': host, 'alias': alias }
                    h = self._controllers.get_id(host)
                    if h:
                        servicegroup = h.get_setup().get('servicetable', '')
                        r1['servicegroup'] = servicegroup
                    else:
                        log.warning('host "%s" with alias "%s" doesnt exists but is in user "%s" hostgroup "%s"', host, alias, user, hostgroup)
                    r['hosts'].append(r1)
        return({ 'status': 200, 'bodydata': r })
