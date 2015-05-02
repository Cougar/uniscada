from sessionexception import SessionException

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
