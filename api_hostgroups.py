from sessionexception import SessionException

class API_hostgroups(object):
    def __init__(self, usersessions, controllers):
        self._usersessions = usersessions
        self._controllers = controllers

    def output(self, user, filter):
        if not filter:
            return self._output_all_hostgroups(user)
        else:
            return self._output_one_hostgroups(user, filter)

    def _output_all_hostgroups(self, user):
        userdata = self._usersessions.find_by_id(user).get_userdata()
        r = []
        if 'hostgroups' in userdata:
            for hostgroup in userdata['hostgroups']:
                r.append({ 'hostgroup': hostgroup, 'alias': userdata['hostgroups'][hostgroup].get('alias', '') })
        return r

    def _output_one_hostgroups(self, user, hostgroup):
        usersession = self._usersessions.find_by_id(user)
        userdata = usersession.get_userdata()
        if not 'hostgroups' in userdata:
            return {}
        if not hostgroup in userdata['hostgroups']:
            raise SessionException('no such hostgroup for this user')
        r = {}
        r['hostgroup'] = hostgroup
        r['hosts'] = []
        if 'members' in userdata['hostgroups'][hostgroup]:
            for host, alias in userdata['hostgroups'][hostgroup]['members'].items():
                if usersession.check_access(host):
                    self._controllers.get_id(host)
                    servicegroup = self._controllers.get_id(host).get_setup().get('servicetable', '')
                    r['hosts'].append({
                        'id': host,
                        'alias': alias,
                        'servicegroup': servicegroup
                        })
        return r
