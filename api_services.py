from sessionexception import SessionException

class API_services(object):
    def __init__(self, core):
        self._core = core
        self._usersessions = self._core.usersessions()
        self._controllers = self._core.controllers()
        self._servicegroups = self._core.servicegroups()

    def output(self, **kwargs):
        if kwargs.get('method', None) == 'GET':
            if kwargs.get('filter', None):
                return self._output_one_service(kwargs.get('user', None), kwargs.get('filter', None))
            else:
                raise SessionException('missing parameter')
        else:
            return({ 'status': 405 })

    def _output_one_service(self, user, controller):
        usersession = self._usersessions.find_by_id(user)
        if not usersession.check_access(controller):
            raise SessionException('unknown controller')
        c = self._controllers.get_id(controller)
        if not c:
            return({ 'status': 404 })
        servicegroup = None
        setup = c.get_setup()
        if setup:
            servicetable = setup.get('servicetable', None)
            if servicetable:
                servicegroup = self._servicegroups.get_id(servicetable)
        return({ 'status': 200, 'bodydata': c.get_service_data_v1(servicegroup) })
