from sessionexception import SessionException

class API_hosts(object):
    def __init__(self, core):
        self._core = core
        self._usersessions = self._core.usersessions()
        self._controllers = self._core.controllers()
        self._hosts = self._core.hosts()

    def output(self, user, filter):
        if not filter:
            return self._output_all_hosts(user)
        else:
            return self._output_one_controller(user, filter)

    def _output_all_hosts(self, user):
        usersession = self._usersessions.find_by_id(user)
        r = []
        for h in self._hosts.get_id_list():
            host = self._hosts.find_by_id(h)
            entry = []
            for controller in host.get_controller_list():
                c = controller.get_id()
                if usersession.check_access(c):
                    entry.append(c)
            if  usersession.is_admin():
                r.append({
                    'host': h,
                    'controllers': entry,
                    'stats': host.get_stats()
                    })
            elif len(entry):
                r.append({ 'host': h, 'controllers': entry })
        return r

    def _output_one_controller(self, user, host):
        usersession = self._usersessions.find_by_id(user)
        if not usersession.check_access(host):
            raise SessionException('unknown host')
        h = self._controllers.get_id(host)
        if not h:
            return {}
        return h.get_host_data_v1(usersession.is_admin())
