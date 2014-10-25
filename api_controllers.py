from sessionexception import SessionException

class API_controllers(object):
    def __init__(self, usersessions, controllers):
        self._usersessions = usersessions
        self._controllers = controllers

    def output(self, user, filter):
        if not filter:
            return self._output_all_controllers(user)
        else:
            return self._output_one_controller(user, filter)

    def _output_all_controllers(self, user):
        usersession = self._usersessions.find_by_id(user)
        r = []
        for controller in self._controllers.get_id_list():
            if usersession.check_access(controller):
                r.append({ 'controller': str(controller) })
        return r

    def _output_one_controller(self, user, controller):
        usersession = self._usersessions.find_by_id(user)
        if not usersession.check_access(controller):
            raise SessionException('unknown controller')
        c = self._controllers.get_id(controller)
        if not c:
            return {}
        r = {}
        r['controller'] = str(controller)
        r['registers'] = []
        for (reg, val, ts) in c.get_state_register_list():
            r['registers'].append({ 'register': reg, 'value': val, 'timestamp': ts })
        return r
