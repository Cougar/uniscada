""" Common functions for API classes.
"""
from schema import SchemaError

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class APIBase(object):
    """ Defaults for API classes
    """

    API_BASE_PATH = '/api/v1'

    def __init__(self, core):
        self._core = core
        self._usersessions = self._core.usersessions()
        self._controllers = self._core.controllers()
        self._servicegroups = self._core.servicegroups()
        self._hosts = self._core.hosts()
        self._wsclients = self._core.wsclients()

    def output(self, **kwargs):
        """ Process HTTP request and output results """
        self._validate_schema(**kwargs)
        if kwargs.get('method', None) == 'GET':
            if kwargs.get('filter', None):
                return self._request_get_with_filter(**kwargs)
            else:
                return self._request_get(**kwargs)
        elif kwargs.get('method', None) == 'POST':
            return self._request_post(**kwargs)
        elif kwargs.get('method', None) == 'DELETE':
            return self._request_delete(**kwargs)
        elif kwargs.get('method', None) == 'PUT':
            return self._request_put(**kwargs)
        else:
            return {'status': 405}

    def _request_get(self, **kwargs):
        """ Process 'GET' request """
        return {'status': 405}

    def _request_get_with_filter(self, **kwargs):
        """ Process 'GET' request with filter """
        return {'status': 405}

    def _request_post(self, **kwargs):
        """ Process 'POST' request """
        return {'status': 405}

    def _request_delete(self, **kwargs):
        """ Process 'DELETE' request """
        return {'status': 405}

    def _request_put(self, **kwargs):
        """ Process 'PUT' request """
        return {'status': 405}

    def _error_if_not_systemuser(self, **kwargs):
        """ Check if request came from 'system' user """
        self._error_if_not_scope('system', **kwargs)

    def _error_if_not_scope(self, scope, **kwargs):
        """ Check if user is in this scope """
        usersession = self._usersessions.get_id(kwargs.get('user', None))
        assert usersession
        if not usersession.check_scope(scope):
            raise UserWarning('no user permission: %s', scope)

    def _get_data_or_error(self, **kwargs):
        """ Return required data or raise Error """
        data = kwargs.get('data', None)
        if not data:
            raise UserWarning('missing data')
        return data

    def _get_filter_or_error(self, errmsg, **kwargs):
        """ Return required filter or raise Error """
        fltr = kwargs.get('filter', None)
        if not fltr:
            raise UserWarning(errmsg)
        return fltr

    def _validate_schema(self, method, **kwargs):
        schema = getattr(self, '_schema_' + method, None)
        if not schema:
            return
        data = kwargs.get('data', None)
        try:
            schema.validate(data)
        except SchemaError as ex:
            log.warning('schema error: ' + str(ex))
            raise UserWarning('data schema error: ' + str(ex))
