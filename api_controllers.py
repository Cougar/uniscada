class API_controllers(object):
    def __init__(self, controllers):
        self._controllers = controllers

    def output(self, user, filter):
        if not filter:
            return self._output_all_controllers(user)
        else:
            return self._output_one_controller(user, filter)

    def _output_all_controllers(self, user):
        # FIXME add user authorization
        r = []
        for controller in self._controllers.get_id_list():
            r.append({ 'controller': str(controller) })
        return r

    def _output_one_controller(self, user, controller):
        # FIXME add user authorization
        c = self._controllers.get_id(controller)
        if not c:
            return {}
        r = {}
        r['controller'] = str(controller)
        r['registers'] = []
        for (reg, val, ts) in c.get_state_register_list():
            r['registers'].append({ 'register': reg, 'value': val, 'timestamp': ts })
        return r
