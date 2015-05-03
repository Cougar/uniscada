from sessionexception import SessionException

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class API_usersessions(object):
    def __init__(self, core):
        self._core = core
        self._usersessions = self._core.usersessions()
        self._wsclients = self._core.wsclients()

    def output(self, **kwargs):
        if not kwargs.get('user', None) == '_system_':
            raise UserWarning('not system user')
        if kwargs.get('method', None) == 'GET':
            if kwargs.get('filter', None):
                return self._output_one_usersession(kwargs.get('filter', None))
            else:
                return self._output_all_usersessions()
        elif kwargs.get('method', None) == 'POST':
            return self._create_usersessions(**kwargs)
        elif kwargs.get('method', None) == 'DELETE':
            return self._delete_usersession(**kwargs)
        else:
            return({ 'status': 405 })

    def _output_all_usersessions(self):
        r = []
        for usersession in self._usersessions.get_id_list():
                r.append({ 'usersession': str(usersession) })
        return({ 'status': 200, 'bodydata': r })

    def _output_one_usersession(self, user):
        u = self._usersessions.get_id(user)
        if not u:
            return({ 'status': 404 })
        return({ 'status': 200, 'bodydata': u.get_usersession_data_v1() })

    def _create_usersessions(self, **kwargs):
        log.debug('_create_usersessions(%s)' % str(kwargs))
        data = kwargs.get('data', None)
        if not data:
            raise UserWarning('missing data')
        if not type(data) == list:
            raise UserWarning('user_name list expected')
        for u in data:
            user = u.get('user_name', None)
            if not user:
                raise UserWarning('user data missing')
            if self._usersessions.get_id(user):
                raise UserWarning('user %s already exists' % user)
        for u in data:
            user = self._usersessions.find_by_id(u.get('user_name', None))
            log.info('new usersession created: %s' % user)
            user.read_userdata_form_nagios()
        return({ 'status': 201, 'headers': [ { 'Location' : '/api/v1/usersessions/' } ] })

    def _delete_usersession(self, **kwargs):
        log.debug('_delete_usersession(%s)' % str(kwargs))
        data = kwargs.get('data', None)
        if data:
            raise UserWarning('unknown data')
        filter = kwargs.get('filter', None)
        if not filter:
            raise UserWarning('user id expected')
        if filter == "_system_":
            raise UserWarning('system user can not be deleted')
        if filter == "*":
            deleted = 0
            for user in list(self._usersessions.get_id_list()):
                if user != "_system_":
                    deleted += 1
                    self._delete_one_usersession(user)
                if not deleted:
                    raise UserWarning('no usersession to delete')
        elif self._usersessions.get_id(filter):
            self._delete_one_usersession(filter)
        else:
            raise UserWarning('no such usersession')
        return({ 'status': 200 })

    def _delete_one_usersession(self, user):
        assert self._usersessions.get_id(user)
        for ws in list(self._wsclients.get_id_list()):
            if ws.user == user:
                log.debug('close ws session: %s', str(ws))
                ws.on_close()
                ws.close()
        # FIXME implement usersession.remove()
        self._usersessions.remove_by_id(user)
