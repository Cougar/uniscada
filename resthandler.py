import tornado.web
import json

from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps

from sessionexception import SessionException

from cookieauth import CookieAuth
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

            if 'status' in result:
                self.set_status(result['status'])

            self.set_header("Content-Type", "application/json; charset=utf-8")
            self.set_header("Access-Control-Allow-Origin", "*")
            if 'headers' in result:
                for header in result['headers']:
                    for key in header:
                        self.set_header(key, header[key])

            self.write(json.dumps(result['bodydata'], indent=4, sort_keys=True, cls=JSONBinEncoder))
            self.finish()

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


class RestHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        self._usersessions = kwargs.pop('usersessions', None)
        self._controllers = kwargs.pop('controllers', None)
        self._wsclients = kwargs.pop('wsclients', None)
        self._msgbus = kwargs.pop('msgbus', None)
        super(RestHandler, self).__init__(*args, **kwargs)

    def initialize(self):
        pass

    def get_current_user(self):
        return CookieAuth(self).get_current_user()

    @unblock
    def get(self, *args, **kwargs):

        self.user = self.get_current_user()
        if self.user == None:
            return({ 'status': 200, 'bodydata': {'message': 'Not authenticated', 'login_url': 'https://login.itvilla.com/login'} })

        if len(args) != 3:
            return({'message' : 'missing arguments'})

        filter = None
        if args[2] != '':
            filter = args[2]

        try:
            self._usersession = self._usersessions.find_by_id(self.user)
            if not self._usersession.get_userdata():
                self._usersession.read_userdata_form_nagois()
                # FIXME return right reload page with 307
                # FIXME add delay to avoid race condition
                # FIXME return right URL
                return({ 'status': 200, 'headers': [ { 'Location': 'https://receiver.itvilla.com:4433/api/v1/hosts' } ], 'bodydata': {'message' : 'Authentication in progress..'} })

            body = API(self._usersessions, self._controllers).get(self.user, args[0], filter)

            headers = [
                    { 'X-Username': self.user }
            ]
            return({ 'status': 200, 'headers': headers, 'bodydata': body })
        except SessionException as e:
            return({ 'status': 500, 'bodydata': {'message' : str(e)} })
        except Exception as e:
            return({ 'status': 501, 'bodydata': {'message' : str(e)} })