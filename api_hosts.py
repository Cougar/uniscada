class API_hosts(object):
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
        for host in self._controllers.get_id_list():
            r.append({ 'host': host })
        return r

    def _output_one_controller(self, user, host):
        # FIXME add user authorization
        h = self._controllers.get_id(host)
        if not h:
            return {}
        r = {}
        r['host'] = host
        r['registers'] = h._state
        r['registers'] = []
        if h._last_sdp:
            for reg in h._last_sdp.get_data_list():
                r1 = {}
                r1['key'] = reg[0]
                r1['value'] = h._last_sdp.get_data(reg[0])
                r['registers'].append(r1)
        return r
