from apibase import APIBase
from sessionexception import SessionException

from schema import Schema, Optional

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class APIservicegroups(APIBase):

    API_PATH = APIBase.API_BASE_PATH + '/servicegroups/'

    _schema_GET = Schema(None)
    _schema_POST = Schema([{
        'servicegroup': str,
        }])
    _schema_DELETE = Schema(None)
    _schema_PUT = Schema([{
        'conv_coef': str,
        'desc0': str,
        'desc1': str,
        'desc2': str,
        Optional('freshness'): str,
        Optional('grp_value'): str,
        'in_unit': str,
        Optional('max_val'): str,
        Optional('min_len'): str,
        Optional('minstep'): str,
        Optional('multicfg'): str,
        Optional('multiperf'): str,
        Optional('multivalue'): str,
        Optional('notify'): str,
        'out_unit': str,
        'sta_reg': str,
        Optional('step'): str,
        'svc_name': str,
        Optional('toggle'): str,
        'val_reg': str,
        }])

    def _get_servicegroupids(self, user):
        usersession = self._usersessions.find_by_id(user)
        assert usersession
        if usersession.check_scope('system'):
            return list(self._servicegroups.get_id_list())
        servicegroupids = usersession.get_servicegroupids()
        if not servicegroupids:
            srvgrps = {}
            for controller in usersession._controllerlist.keys():
                c = self._controllers.get_id(controller)
                if not c:
                    continue
                servicegroup = c.get_setup().get('servicetable', None)
                if servicegroup and servicegroup != '':
                    srvgrps[servicegroup] = True
            servicegroupids = list(srvgrps.keys())
            usersession.set_servicegroupids(servicegroupids)
        return servicegroupids

    def _request_get(self, **kwargs):
        """ Return list of all servicegroups """
        log.debug('_request_get(%s)', str(kwargs))
        user = kwargs.get('user', None)
        servicegroupids = self._get_servicegroupids(user)
        r = []
        for servicegroup in servicegroupids:
            r.append({'servicegroup': servicegroup})
        return {'status': 200, 'bodydata': r}

    def _request_get_with_filter(self, **kwargs):
        """ Return details of one servicegroup """
        log.debug('_request_get_with_filter(%s)', str(kwargs))
        user = kwargs.get('user', None)
        servicegroupids = self._get_servicegroupids(user)
        r = []
        for servicegroup in kwargs.get('filter', '').split(','):
            if servicegroup not in servicegroupids:
                raise SessionException('unknown servicegroup')
            sg = self._servicegroups.get_id(servicegroup)
            if not sg:
                log.error('servicegroup data inconsistency user=%s, ' \
                    ' servicegroup=%s', str(user), str(servicegroup))
                raise SessionException('servicegroup data inconsistency')
            r.append(sg.get_servicegroup_data_v1())
        return {'status': 200, 'bodydata': r}

    def _request_post(self, **kwargs):
        """ Create new servicegroup(s) """
        log.debug('_request_post(%s)', str(kwargs))
        self._error_if_not_systemuser(**kwargs)
        data = kwargs.get('data', None)
        for sg in data:
            servicegroup = sg.get('servicegroup', None)
            if not servicegroup:
                raise UserWarning('servicegroup data missing')
            if self._servicegroups.get_id(servicegroup):
                raise UserWarning('servicegroup %s already exists' % \
                    servicegroup)
        for sg in data:
            sgname = sg.get('servicegroup', None)
            servicegroup = self._servicegroups. \
                find_by_id(sgname)
            log.info('new servicegroup created: %s', servicegroup)
        return {'status': 201, \
            'headers': [{'Location': self.API_PATH}]}

    def _request_delete(self, **kwargs):
        """ Delete existing servicegroup """
        log.debug('_request_delete(%s)', str(kwargs))
        self._error_if_not_systemuser(**kwargs)
        data = kwargs.get('data', None)
        fltr = kwargs.get('filter', None)
        if not fltr:
            raise UserWarning('servicegroup name expected')
        servicegroup = self._servicegroups.get_id(fltr)
        if not servicegroup:
            raise UserWarning('no such servicegroup')
        # FIXME implement servicegroup.remove()
        self._servicegroups.remove_by_id(fltr)
        return {'status': 200}

    def _request_put(self, **kwargs):
        """ Setup existing servicegroup """
        log.debug('_request_put(%s)', str(kwargs))
        self._error_if_not_systemuser(**kwargs)
        data = kwargs.get('data', None)
        fltr = kwargs.get('filter', None)
        if not fltr:
            raise UserWarning('servicegroup name expected')
        servicegroup = self._servicegroups.get_id(fltr)
        if not servicegroup:
            raise UserWarning('no such servicegroup')
        for service in data:
            servicegroup.set_service(service)
        return {'status': 200}
