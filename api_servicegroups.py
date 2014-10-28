from sessionexception import SessionException

class API_servicegroups(object):
    def __init__(self, usersessions, controllers, servicegroups):
        self._usersessions = usersessions
        self._controllers = controllers
        self._servicegroups = servicegroups

    def output(self, user, filter):
        if not filter:
            return self._output_all_servicegroups(user)
        else:
            return self._output_one_servicegroup(user, filter)

    def _get_servicegroupids(self, user):
        usersession = self._usersessions.find_by_id(user)
        servicegroupids = usersession.get_servicegroupids()
        if not servicegroupids:
            srvgrps = {}
            for controller in usersession._controllerlist.keys():
                c = self._controllers.get_id(controller)
                servicegroup = c.get_setup().get('servicetable', None)
                if servicegroup and servicegroup != '':
                    srvgrps[servicegroup] = True
            servicegroupids = list(srvgrps.keys())
            usersession.set_servicegroupids(servicegroupids)
        return servicegroupids

    def _output_all_servicegroups(self, user):
        servicegroupids = self._get_servicegroupids(user)
        r = []
        for servicegroup in servicegroupids:
            r.append({ 'servicegroup': servicegroup })
        return r

    def _output_one_servicegroup(self, user, servicegroup):
        servicegroupids = self._get_servicegroupids(user)
        if servicegroup not in servicegroupids:
            raise SessionException('unknown servicegroup')
        sg = self._servicegroups.get_id(servicegroup)
        if not sg:
            log.error('servicegroup data inconsistency user=%s, servicegroup=%s', str(user), str(servicegroup))
            raise SessionException('servicegroup data inconsistency')
        return sg.get_servicegroup_data_v1()
