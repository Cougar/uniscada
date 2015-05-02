import tornado.web
import json

from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps

from sessionexception import SessionException

from api import API

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'RestHandler',
    'get',
]

EXECUTOR = ThreadPoolExecutor(max_workers=50)

def unblock(f):
    @tornado.web.asynchronous
    @wraps(f)

    def wrapper(*args, **kwargs):
        self = args[0]

        def callback(future):
            result = future.result()
            self.write_response(result)

        EXECUTOR.submit(
            partial(f, *args, **kwargs)
        ).add_done_callback(
            lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                partial(callback, future)))

    return wrapper


class JSONBinEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) == type(bytes()):
            return obj.decode(encoding='UTF-8')
        return json.JSONEncoder.default(self, obj)

from tornado_content_negotiation import ContentNegotiation

class RestHandler(ContentNegotiation, tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        self._core = kwargs.pop('core', None)
        self._usersessions = self._core.usersessions()
        self._controllers = self._core.controllers()
        self._servicegroups = self._core.servicegroups()
        self._wsclients = self._core.wsclients()
        self._msgbus = self._core.msgbus()
        content_types = ['application/json; charset=UTF-8']
        super(RestHandler, self).__init__(negotiable_server_content_types=content_types, *args, **kwargs)

    def initialize(self):
        pass

    def get_current_user(self):
        return self._core.auth().get_user(host=self.request.host, headers=self.request.headers, cookiehandler=self.get_cookie)

    def write_response(self, result):
        if self._finished:
            return

        if 'status' in result:
            self.set_status(result['status'])

        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.set_header("Access-Control-Allow-Origin", "*")
        if 'headers' in result:
            for header in result['headers']:
                for key in header:
                    self.set_header(key, header[key])

        if 'bodydata' in result:
            self.write(json.dumps(result['bodydata'], indent=4, sort_keys=True, cls=JSONBinEncoder))
        self.finish()

    def precheck(self):
        ct = self.negotiated_content_type(finish_on_error=False)
        if not ct:
            self.write_response({ 'status': 406, 'bodydata': {'message' : 'unsupportet content type'} })
            return False
        self.user = self.get_current_user()
        if not self.user:
            self.write_response({ 'status': 200, 'bodydata': {'message': 'Not authenticated', 'login_url': 'https://login.uniscada.eu/login'} })
            return False
        self._usersession = self._usersessions.find_by_id(self.user)
        if not self._usersession.get_userdata():
            self._usersession.read_userdata_form_nagois()
            # FIXME return right reload page with 307
            # FIXME add delay to avoid race condition
            # FIXME return right URL
            self.write_response({ 'status': 200, 'headers': [ { 'Location': 'https://api.uniscada.eu/api/v1/hosts' } ], 'bodydata': {'message' : 'Authentication is in progress..'} })
            return False
        return True

    @unblock
    def post(self, *args, **kwargs):
        log.debug('POST: args = %s, kwargs = %s self = %s' % (str(args), str(**kwargs), str(self.__dict__)))
        return self._any_method(*args, **kwargs)

    @unblock
    def delete(self, *args, **kwargs):
        log.debug('DELETE: args = %s, kwargs = %s self = %s' % (str(args), str(**kwargs), str(self.__dict__)))
        return self._any_method(*args, **kwargs)

    @unblock
    def put(self, *args, **kwargs):
        log.debug('PUT: args = %s, kwargs = %s self = %s' % (str(args), str(**kwargs), str(self.__dict__)))
        return self._any_method(*args, **kwargs)

    @unblock
    def get(self, *args, **kwargs):
        log.debug('GET: args = %s, kwargs = %s self = %s' % (str(args), str(**kwargs), str(self.__dict__)))
        return self._any_method(*args, **kwargs)

    def _any_method(self, *args, **kwargs):
        if not self.precheck():
            return

        if len(args) != 3:
            return({ 'status': 200, 'bodydata': {'message' : 'missing arguments'} })

        filter = None
        if args[2] != '':
            filter = args[2]

        data = None
        if self.request.body:
            try:
                data = json.loads(self.request.body.decode('UTF8'))
            except Exception as e:
                log.warning("JSON parse error: %s" % str(e))
                pass

        try:
            return API(self._core).get(user=self.user, resource=args[0], filter=filter, method=self.request.method, data=data)
        except SessionException as e:
            return({ 'status': 500, 'bodydata': {'message' : str(e)} })
        except UserWarning as e:
            return({ 'status': 500, 'bodydata': {'message' : 'error: %s' % str(e)} })
        except Exception as e:
            log.critical("Exception: %s" % str(e))
            import traceback
            log.critical("Trace: %s" % traceback.format_exc())
            return({ 'status': 501, 'bodydata': {'message' : str(e)} })
