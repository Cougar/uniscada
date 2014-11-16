from sessionexception import SessionException

class API_hosts(object):
    def __init__(self, core):
        self._core = core
        self._usersessions = self._core.usersessions()
        self._controllers = self._core.controllers()

    def output(self, user, filter):
        if not filter:
            return self._output_all_controllers(user)
        else:
            return self._output_one_controller(user, filter)

    def _output_all_controllers(self, user):
        usersession = self._usersessions.find_by_id(user)
        r = []
        for host in self._controllers.get_id_list():
            if usersession.check_access(host):
                r.append({ 'host': host })
        return r

    def _output_one_controller(self, user, host):
        usersession = self._usersessions.find_by_id(user)
        if not usersession.check_access(host):
            raise SessionException('unknown host')
        h = self._controllers.get_id(host)
        if not h:
            return {}
        return h.get_host_data_v1()
