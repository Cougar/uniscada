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
        elif kwargs.get('method', None) == 'POST':
            return self._create_servicegroups(**kwargs)
        elif kwargs.get('method', None) == 'DELETE':
            return self._delete_servicegroup(**kwargs)
        elif kwargs.get('method', None) == 'PUT':
            return self._setup_servicegroup(**kwargs)
        else:
            return({ 'status': 405 })

    def _get_servicegroupids(self, user):
        if user == '_system_':
            return list(self._servicegroups.get_id_list())
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

    def _create_servicegroups(self, **kwargs):
        log.debug('_create_servicegroup(%s)' % str(kwargs))
        if not kwargs.get('user', None) == '_system_':
            raise UserWarning('not system user')
        data = kwargs.get('data', None)
        if not data:
            raise UserWarning('missing data')
        if not type(data) == list:
            raise UserWarning('servicegroup list expected')
        for sg in data:
            servicegroup = sg.get('servicegroup', None)
            if not servicegroup:
                raise UserWarning('servicegroup data missing')
            if self._servicegroups.get_id(servicegroup):
                raise UserWarning('servicegroup %s already exists' % servicegroup)
        for sg in data:
            servicegroup = self._servicegroups.find_by_id(sg.get('servicegroup', None))
            log.info('new servicegroup created: %s' % servicegroup)
        return({ 'status': 201, 'headers': [ { 'Location' : '/api/v1/servicegroups/' } ] })

    def _delete_servicegroup(self, **kwargs):
        log.debug('_delete_servicegroup(%s)' % str(kwargs))
        if not kwargs.get('user', None) == '_system_':
            raise UserWarning('not system user')
        data = kwargs.get('data', None)
        if data:
            raise UserWarning('unknown data')
        filter = kwargs.get('filter', None)
        if not filter:
            raise UserWarning('servicegroup name expected')
        servicegroup = self._servicegroups.get_id(filter)
        if not servicegroup:
            raise UserWarning('no such servicegroup')
        # FIXME implement servicegroup.remove()
        self._servicegroups.remove_by_id(filter)
        return({ 'status': 200 })

    def _setup_servicegroup(self, **kwargs):
        log.debug('_setup_servicegroup(%s)' % str(kwargs))
        if not kwargs.get('user', None) == '_system_':
            raise UserWarning('not system user')
        data = kwargs.get('data', None)
        if not data:
            raise UserWarning('missing data')
        filter = kwargs.get('filter', None)
        if not filter:
            raise UserWarning('servicegroup name expected')
        servicegroup = self._servicegroups.get_id(filter)
        if not servicegroup:
            raise UserWarning('no such servicegroup')
        for service in data:
            servicegroup._services.find_by_id(service['sta_reg']).set_setup(service)
        return({ 'status': 200 })
