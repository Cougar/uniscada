from apibase import APIBase

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class APIusersessions(APIBase):

    API_PATH = APIBase.API_BASE_PATH + '/usersessions/'

    def _request_get(self, **kwargs):
        """ Return list of all usersessions """
        log.debug('_request_get(%s)', str(kwargs))
        self._error_if_not_systemuser(**kwargs)
        r = []
        for usersession in self._usersessions.get_id_list():
            r.append({'usersession': str(usersession)})
        return {'status': 200, 'bodydata': r}

    def _request_get_with_filter(self, **kwargs):
        """ Return details of one usersession """
        log.debug('_request_get_with_filter(%s)', str(kwargs))
        self._error_if_not_systemuser(**kwargs)
        user = kwargs.get('filter', None)
        u = self._usersessions.get_id(user)
        if not u:
            return {'status': 404}
        return {'status': 200, 'bodydata': u.get_usersession_data_v1()}

    def _request_post(self, **kwargs):
        """ Create new usersession """
        log.debug('_request_post(%s)', str(kwargs))
        self._error_if_not_systemuser(**kwargs)
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
            log.info('new usersession created: %s', user)
            user.read_userdata_form_nagios()
        return {'status': 201, \
            'headers': [{'Location' : self.API_PATH}]}

    def _request_delete(self, **kwargs):
        """ Delete existing usersession """
        log.debug('_request_delete(%s)', str(kwargs))
        self._error_if_not_systemuser(**kwargs)
        data = kwargs.get('data', None)
        if data:
            raise UserWarning('unknown data')
        fltr = kwargs.get('filter', None)
        if not fltr:
            raise UserWarning('user id expected')
        deleted = 0
        if fltr == "*":
            for user in list(self._usersessions.get_id_list()):
                deleted += self._delete_one_usersession(user)
            if not deleted:
                raise UserWarning('no usersession to delete')
        elif self._usersessions.get_id(fltr):
            if not self._delete_one_usersession(fltr):
                raise UserWarning('system user can not be deleted')
        else:
            raise UserWarning('no such usersession')
        return {'status': 200, \
            'bodydata': {'message': 'usersessions deleted: %d' % deleted}}

    def _delete_one_usersession(self, user):
        """ Delete existing usersession """
        usersession = self._usersessions.get_id(user)
        assert usersession
        if usersession.check_scope('system'):
            return 0
        for ws in list(self._wsclients.get_id_list()):
            if ws.user == user:
                log.debug('close ws session: %s', str(ws))
                ws.on_close()
                ws.close()
        # FIXME implement usersession.remove()
        self._usersessions.remove_by_id(user)
        return 1
