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
        for id in self._controllers.get_id_list():
            r.append({ 'controller': str(id) })
        return r

    def _output_one_controller(self, user, id):
        # FIXME add user authorization
        controller = self._controllers.get_id(id)
        if not controller:
            return {}
        r = {}
        r['controller'] = str(id)
        r['registers'] = []
        for (reg, val, ts) in controller.get_state_register_list():
            r['registers'].append({ 'register': reg, 'value': val, 'timestamp': ts })
        return r
