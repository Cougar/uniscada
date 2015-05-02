from sessionexception import SessionException

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class API_servicegroups(object):
    def __init__(self, core):
        self._core = core
        self._usersessions = self._core.usersessions()
        self._controllers = self._core.controllers()
        self._servicegroups = self._core.servicegroups()

    def output(self, **kwargs):
        if kwargs.get('method', None) == 'GET':
            if kwargs.get('filter', None):
                return self._output_one_servicegroup(kwargs.get('user', None), kwargs.get('filter', None))
            else:
                return self._output_all_servicegroups(kwargs.get('user', None))
        else:
            return({ 'status': 405 })

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
        return({ 'status': 200, 'bodydata': r })

    def _output_one_servicegroup(self, user, servicegroup):
        servicegroupids = self._get_servicegroupids(user)
        if servicegroup not in servicegroupids:
            raise SessionException('unknown servicegroup')
        sg = self._servicegroups.get_id(servicegroup)
        if not sg:
            log.error('servicegroup data inconsistency user=%s, servicegroup=%s', str(user), str(servicegroup))
            raise SessionException('servicegroup data inconsistency')
        return({ 'status': 200, 'bodydata': sg.get_servicegroup_data_v1() })
