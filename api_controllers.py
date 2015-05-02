from sessionexception import SessionException

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class API_controllers(object):
    def __init__(self, core):
        self._core = core
        self._usersessions = self._core.usersessions()
        self._controllers = self._core.controllers()
        self._servicegroups = self._core.servicegroups()

    def output(self, **kwargs):
        if kwargs.get('method', None) == 'GET':
            if kwargs.get('filter', None):
                return self._output_one_controller(kwargs.get('user', None), kwargs.get('filter', None))
            else:
                return self._output_all_controllers(kwargs.get('user', None))
        elif kwargs.get('method', None) == 'POST':
            return self._create_controllers(**kwargs)
        elif kwargs.get('method', None) == 'DELETE':
            return self._delete_controller(**kwargs)
        elif kwargs.get('method', None) == 'PUT':
            return self._setup_controller(**kwargs)
        else:
            return({ 'status': 405 })

    def _output_all_controllers(self, user):
        usersession = self._usersessions.find_by_id(user)
        r = []
        for controller in self._controllers.get_id_list():
            if usersession.check_access(controller):
                r.append({ 'controller': str(controller) })
        return({ 'status': 200, 'bodydata': r })

    def _output_one_controller(self, user, controller):
        usersession = self._usersessions.find_by_id(user)
        if not usersession.check_access(controller):
            raise SessionException('unknown controller')
        c = self._controllers.get_id(controller)
        if not c:
            return({ 'status': 404 })
        return({ 'status': 200, 'bodydata': c.get_controller_data_v1() })

    def _create_controllers(self, **kwargs):
        log.debug('_create_controller(%s)' % str(kwargs))
        if not kwargs.get('user', None) == '_system_':
            raise UserWarning('not system user')
        data = kwargs.get('data', None)
        if not data:
            raise UserWarning('missing data')
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
            log.info('new controller created: %s' % controller)
        return({ 'status': 201, 'headers': [ { 'Location' : '/api/v1/controllers/' } ] })

    def _delete_controller(self, **kwargs):
        log.debug('_delete_controller(%s)' % str(kwargs))
        if not kwargs.get('user', None) == '_system_':
            raise UserWarning('not system user')
        data = kwargs.get('data', None)
        if data:
            raise UserWarning('unknown data')
        filter = kwargs.get('filter', None)
        if not filter:
            raise UserWarning('controller id expected')
        controller = self._controllers.get_id(filter)
        if not controller:
            raise UserWarning('no such controller')
        # FIXME implement controller.remove()
        self._controllers.remove_by_id(filter)
        return({ 'status': 200 })

    def _setup_controller(self, **kwargs):
        log.debug('_setup_controller(%s)' % str(kwargs))
        if not kwargs.get('user', None) == '_system_':
            raise UserWarning('not system user')
        data = kwargs.get('data', None)
        if not data:
            raise UserWarning('missing data')
        filter = kwargs.get('filter', None)
        if not filter:
            raise UserWarning('controller id expected')
        controller = self._controllers.get_id(filter)
        if not controller:
            raise UserWarning('no such controller')
        if not "servicetable" in data:
            raise UserWarning('servicetable not defined')
        if not self._servicegroups.get_id(data["servicetable"]):
            raise UserWarning('no such servicegroup defined: %s' % data["servicetable"])
        setup = controller.get_setup()
        setup.update(data)
        controller.set_setup(setup)
        return({ 'status': 200 })
