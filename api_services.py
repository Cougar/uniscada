from sessionexception import SessionException

class API_services(object):
    def __init__(self, core):
        self._core = core
        self._usersessions = self._core.usersessions()
        self._controllers = self._core.controllers()

    def output(self, user, filter):
        if not filter:
            raise SessionException('missing parameter')
        else:
            return self._output_one_service(user, filter)

    def _output_one_service(self, user, controller):
        usersession = self._usersessions.find_by_id(user)
        if not usersession.check_access(controller):
            raise SessionException('unknown controller')
        c = self._controllers.get_id(controller)
        if not c:
            return {}
        return c.get_service_data_v1()
