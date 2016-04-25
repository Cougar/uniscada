from apibase import APIBase
from sessionexception import SessionException

from schema import Schema, Optional

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class APIcontrollers(APIBase):

    API_PATH = APIBase.API_BASE_PATH + '/controllers/'

    _schema_GET = Schema(None)
    _schema_POST = Schema([{
        'controller': str,
        }])
    _schema_DELETE = Schema(None)
    _schema_PUT = Schema({
        Optional('disp_name'): str,
        'it_sim': str,
        'location': str,
        'mac': str,
        'servicetable': str,
        Optional('nagios_ip'): str,
        Optional('nagios_port'): str,
        Optional('secret_key'): str,
        Optional('ignore'): bool,
        Optional('script'): str,
        Optional('babup_server'): str,
        Optional('babup_services'): str,
        Optional('babup_user'): str,
        Optional('babup_pass'): str,
        Optional('grp_value'): str,
        })

    def _request_get(self, **kwargs):
        """ Return list of all controllers """
        log.debug('_request_get(%s)', str(kwargs))
        user = kwargs.get('user', None)
        usersession = self._usersessions.find_by_id(user)
        r = []
        for controller in self._controllers.get_id_list():
            if usersession.check_access(controller):
                r.append({'controller': str(controller)})
        return {'status': 200, 'bodydata': r}

    def _request_get_with_filter(self, **kwargs):
        """ Return details of one controller """
        log.debug('_request_get_with_filter(%s)', str(kwargs))
        user = kwargs.get('user', None)
        usersession = self._usersessions.find_by_id(user)
        r = []
        for controller in kwargs.get('filter', '').split(','):
            if not usersession.check_access(controller):
                raise SessionException('unknown controller')
            c = self._controllers.get_id(controller)
            if not c:
                raise SessionException('unknown controller')
            r.append(c.get_controller_data_v1())
        return {'status': 200, 'bodydata': r}

    def _request_post(self, **kwargs):
        """ Create new controller """
        log.debug('_request_post(%s)', str(kwargs))
        self._error_if_not_systemuser(**kwargs)
        data = self._get_data_or_error(**kwargs)
        if not type(data) == list:
            raise UserWarning('controller list expected')
        for c in data:
            controller = c.get('controller', None)
            if not controller:
                raise UserWarning('controller data missing')
            if self._controllers.get_id(controller):
                raise UserWarning('controller %s already exists' % controller)
        for c in data:
            controller = self._controllers.find_by_id(c.get('controller', None))
            controller.set_servicegroups(self._core.servicegroups())
            controller.set_msgbus(self._core.msgbus())
            log.info('new controller created: %s', controller)
        return {'status': 201, \
            'headers': [{'Location': self.API_PATH}]}

    def _request_delete(self, **kwargs):
        """ Delete existing controller """
        log.debug('_request_delete(%s)', str(kwargs))
        self._error_if_not_systemuser(**kwargs)
        fltr = self._get_filter_or_error('controller id expected', \
            **kwargs)
        self._get_controller_or_error(fltr)
        # FIXME implement controller.remove()
        self._controllers.remove_by_id(fltr)
        return {'status': 200}

    def _request_put(self, **kwargs):
        """ Setup existing controller """
        log.debug('_request_put(%s)', str(kwargs))
        self._error_if_not_systemuser(**kwargs)
        data = self._get_data_or_error(**kwargs)
        fltr = self._get_filter_or_error('controller id expected', \
            **kwargs)
        controller = self._get_controller_or_error(fltr)
        if not "servicetable" in data:
            raise UserWarning('servicetable not defined')
        if not self._servicegroups.get_id(data["servicetable"]):
            raise UserWarning('no such servicegroup defined: %s' % \
                data["servicetable"])
        setup = controller.get_setup()
        setup.update(data)
        controller.set_setup(setup)
        return {'status': 200}

    def _get_controller_or_error(self, fltr):
        """ Get existing controller id or raise Error if missing """
        controller = self._controllers.get_id(fltr)
        if not controller:
            raise UserWarning('no such controller')
        return controller
