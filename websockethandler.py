import tornado.websocket
import json

from api import API

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'WebSocketHandler',
    'open', 'on_message', 'on_close',
]

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        self._core = kwargs.pop('core', None)
        self._usersessions = self._core.usersessions()
        self._controllers = self._core.controllers()
        self._servicegroups = self._core.servicegroups()
        self._wsclients = self._core.wsclients()
        self._msgbus = self._core.msgbus()
        self._authenticated = False
        self._args = args
        super(WebSocketHandler, self).__init__(*args, **kwargs)

    def open(self, *args):
        self.wsclient = self._wsclients.find_by_id(self)
        self.user = self._core.auth().get_user(self.get_cookie)
        self._api = API(self._core)
        if not self.user:
            self.write_message(json.dumps({'message': 'Not authenticated', 'login_url': 'https://login.itvilla.com/login'}, indent=4, sort_keys=True))
            return
        try:
            self._usersession = self._usersessions.find_by_id(self.user)
            if self._usersession.get_userdata():
                self._userauth_done()
            else:
                self._usersession.read_userdata_form_nagois(callback = self._userauth_done)
        except Exception as e:
            self.write_message(json.dumps({'message': 'error: ' + str(e)}))
            return

    def _userauth_done(self):
        log.info('_userauth_done()')
        userdata = self._usersessions.find_by_id(self.user).get_userdata()
        if not userdata:
            log.error('didnt get userdata')
            self.write_message(json.dumps({'message': 'Authentication error', 'login_url': 'https://login.itvilla.com/login'}, indent=4, sort_keys=True))
            self.close()
        elif userdata.get('user_name', None) != self.user:
            log.error('userdata username mismatch: %s : %s', str(userdata.get('user_name', None)), self.user)
            self.write_message(json.dumps({'message': 'Authentication error', 'login_url': 'https://login.itvilla.com/login'}, indent=4, sort_keys=True))
            self.close()
            # FIXME remove UserSession instance after such event
        else:
            self._authenticated = True

    def on_message(self, message):
        if not self.user:
           self.wsclient.send_data({'message': 'Not authenticated', 'login_url': 'https://login.itvilla.com/login'})
           return

        if not self._authenticated:
            self.wsclient.send_data({'message': 'Authentication in progress...'})
            return

        try:
            jsondata = json.loads(message)
        except:
            self.wsclient.send_data({'message': str(sys.exc_info()[1])})
            return

        method = jsondata.get('method', None)
        token = jsondata.get('token', None)
        resource = jsondata.get('resource', None)

        reply = {}

        if token:
            reply['token'] = token

        if not method:
            reply['message'] = 'error: method missing'
            self.wsclient.send_data(reply)
            return

        if method == 'disconnect':
            self.close()
            self.on_close()
            return

        if method not in ['get', 'subscribe', 'unsubscribe']:
            reply['message'] = 'error: unknown method'
            self.wsclient.send_data(reply)
            return

        if not resource:
            reply['message'] = 'error: resource missing'
            self.wsclient.send_data(reply)
            return

        reply['resource'] = resource
        (root, query, filter) = (resource + '//').split('/', 3)[0:3]

        if root != '':
            reply['message'] = 'error: resource path must be absolute'
            self.wsclient.send_data(reply)
            return

        if query not in ['hosts', 'controllers', 'hostgroups', 'servicegroups', 'services']:
            reply['message'] = 'error: unknown resource'
            self.wsclient.send_data(reply)
            return

        if method == 'get':
            try:
                r = self._api.get(user=self.user, resource=query, filter=filter, method='GET')
                reply['body'] = r.get('bodydata', '')
            except Exception as e:
                reply['message'] = 'error: ' + str(e)
        elif method == 'subscribe':
            usersession = self._usersessions.find_by_id(self.user)
            if not usersession.check_access(filter):
                reply['message'] = 'error: no such resource'
                self.wsclient.send_data(reply)
                return

            self._msgbus.subscribe(token, resource, self, self._on_bus_message)
            reply['message'] = 'success'
            reply['body'] = {}
        elif method == 'unsubscribe':
            usersession = self._usersessions.find_by_id(self.user)
            try:
                self._msgbus.unsubscribe(token, resource, self)
                reply['message'] = 'success'
                reply['body'] = {}
            except Exception as e:
                reply['message'] = 'error: ' + str(e)
        else:
            raise Exception('update known method list above')

        self.wsclient.send_data(reply)

    def _on_bus_message(self, token, subject, data):
        log.info("_on_bus_message(%s, %s, %s)", str(token), str(subject), str(data))
        if token:
            data['token'] = token
        self.wsclient.send_data(data)

    def on_close(self):
        self._msgbus.unsubscribe_all(self)
        self._wsclients.remove_by_id(self)

    def __str__(self):
        return(str(self._args))
