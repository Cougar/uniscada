#!/usr/bin/python3

"""
Test URLs (default port, user=sdmarianne)

GOOD
    http://receiver.itvilla.com:8888/api/v1/hostgroups
    http://receiver.itvilla.com:8888/api/v1/hostgroups/
    http://receiver.itvilla.com:8888/api/v1/hostgroups/saared
    http://receiver.itvilla.com:8888/api/v1/servicegroups
    http://receiver.itvilla.com:8888/api/v1/servicegroups/
    http://receiver.itvilla.com:8888/api/v1/servicegroups/service_pumplad_ee
    http://receiver.itvilla.com:8888/api/v1/servicegroups/service_pumplad4_ee
    http://receiver.itvilla.com:8888/api/v1/services/00204AB80D57
    http://receiver.itvilla.com:8888/api/v1/services/00204AB80BF9
    http://receiver.itvilla.com:8888/api/v1/services/00204AA95C56

    https://receiver.itvilla.com:4433/api/v1/hostgroups
    https://receiver.itvilla.com:4433/api/v1/hostgroups/
    https://receiver.itvilla.com:4433/api/v1/hostgroups/saared
    https://receiver.itvilla.com:4433/api/v1/servicegroups
    https://receiver.itvilla.com:4433/api/v1/servicegroups/
    https://receiver.itvilla.com:4433/api/v1/servicegroups/service_pumplad_ee
    https://receiver.itvilla.com:4433/api/v1/servicegroups/service_pumplad4_ee
    https://receiver.itvilla.com:4433/api/v1/services/00204AB80D57
    https://receiver.itvilla.com:4433/api/v1/services/00204AB80BF9
    https://receiver.itvilla.com:4433/api/v1/services/00204AA95C56

BAD
    http://receiver.itvilla.com:8888/
    http://receiver.itvilla.com:8888/api/v1/
    http://receiver.itvilla.com:8888/api/v1/hostgroups/x
    http://receiver.itvilla.com:8888/api/v1/hostgroups/itvilla
    http://receiver.itvilla.com:8888/api/v1/servicegroups/x
    http://receiver.itvilla.com:8888/api/v1/servicegroups/hvvmon_ee
    http://receiver.itvilla.com:8888/api/v1/services/x
    http://receiver.itvilla.com:8888/api/v1/services/0008E101A8E9

    https://receiver.itvilla.com:4433/
    https://receiver.itvilla.com:4433/api/v1/
    https://receiver.itvilla.com:4433/api/v1/hostgroups/x
    https://receiver.itvilla.com:4433/api/v1/hostgroups/itvilla
    https://receiver.itvilla.com:4433/api/v1/servicegroups/x
    https://receiver.itvilla.com:4433/api/v1/servicegroups/hvvmon_ee
    https://receiver.itvilla.com:4433/api/v1/services/x
    https://receiver.itvilla.com:4433/api/v1/services/0008E101A8E9

"""

# Too old distro (Red Hat Enterprise Linux Server release 6.2 (Santiago) / 6 December 2011)
import sys
sys.path.append('/root/tornado-3.2/')
sys.path.append('/root/backports.ssl_match_hostname-3.4.0.2/src')

import logging
import sys
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

import datetime

from monpanel import *

import tornado.web
import tornado.gen
import tornado.websocket

from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps

from udpcomm import *
from controllers import Controllers
from sdpreceiver import SDPReceiver
from wsclients import WsClients

log = logging.getLogger(__name__)

EXECUTOR = ThreadPoolExecutor(max_workers=50)

wsclients = []

class CookieAuth:
    def __init__(self, handler):
        self.handler = handler

    def get_current_user(self):
        try:
            cookeiauth = self.handler.get_cookie('itvilla_com', None)
            if cookeiauth == None:
                return None
            return cookeiauth.split(':')[0]
        except:
            return None


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


class UnknownHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass

    def get(self, *args, **kwargs):
        self.set_status(404)
        base_url = self.request.protocol + '://' + self.request.host
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({
            'message': 'Not Found',
            'api_url': base_url + '/api/v1/'
        }, indent = 4, sort_keys = True))
        self.finish()


class RootHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass

    def get(self, *args, **kwargs):
        base_url = self.request.protocol + '://' + self.request.host
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({
            'hostgroup_url': base_url + '/api/v1/hostgroups{/name}',
            'servicegroup_url': base_url + '/api/v1/servicegroups{/name}',
            'service_url': base_url + '/api/v1/services/name',
            'websocket_url': base_url.replace('http', 'ws', 1) + '/api/v1/ws'
        }, indent = 4, sort_keys = True))
        self.finish()


class RestHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        self._controllers = kwargs.pop('controllers', None)
        self._wsclients = kwargs.pop('wsclients', None)
        super(RestHandler, self).__init__(*args, **kwargs)

    def initialize(self):
        pass

    def get_current_user(self):
        return CookieAuth(self).get_current_user()

    @unblock
    def get(self, *args, **kwargs):

        user = self.get_current_user()
        if user == None:
            return({ 'status': 200, 'bodydata': {'message': 'Not authenticated', 'login_url': 'https://login.itvilla.com/login'} })

        if len(args) != 3:
            return({'message' : 'missing arguments'})

        self.session = Session(user)

        filter = None
        if args[2] != '':
            filter = args[2]

        try:
            body = self.session.sql2json(args[0], filter)

            headers = [
                    { 'X-Username': user }
            ]
            return({ 'status': 200, 'headers': headers, 'bodydata': body })
        except SessionAuthenticationError as e:
            return({ 'status': 200, 'bodydata': {'message' : str(e)} })
        except SessionException as e:
            return({ 'status': 500, 'bodydata': {'message' : str(e)} })
        except Exception as e:
            return({ 'status': 501, 'bodydata': {'message' : str(e)} })


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        self._controllers = kwargs.pop('controllers', None)
        self._wsclients = kwargs.pop('wsclients', None)
        super(WebSocketHandler, self).__init__(*args, **kwargs)

    def open(self, *args):
        self.wsclient = self._wsclients.find_by_id(self)
        cookeiauth = CookieAuth(self)
        self.user = cookeiauth.get_current_user()
        if self.user == None:
            self.write_message(json.dumps({'message': 'Not authenticated', 'login_url': 'https://login.itvilla.com/login'}, indent=4, sort_keys=True))
            return
        try:
            self.session = Session(self.user)
        except Exception as e:
            self.write_message(json.dumps({'message': 'error: ' + str(e)}))
            return

    def on_message(self, message):
        if self.user  == None:
            self.write_message(json.dumps({'message': 'Not authenticated', 'login_url': 'https://login.itvilla.com/login'}, indent=4, sort_keys=True))
            return

        try:
            jsondata = json.loads(message)
        except:
            self.write_message(json.dumps({'message': str(sys.exc_info()[1])}))
            return

        method = jsondata.get('method', None)
        token = jsondata.get('token', None)
        resource = jsondata.get('resource', None)
        resources = []

        reply = {}

        if resource != None:
            resources = resource.split('/')
            reply['resource'] = resource

        if token != None:
            reply['token'] = token

        if method == 'get':
            filter = None
            if len(resources) == 3:
                filter = resources[2]

            try:
                reply['body'] = self.session.sql2json(resources[1], filter)
            except Exception as e:
                reply['message'] = 'error: ' + str(e)

        self.write_message(json.dumps(reply, indent=4, sort_keys=True))

    def on_close(self):
        self._wsclients.remove_by_id(self)

class FileHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.render(args[0])

class UDPReader(object):
    def __init__(self, addr, port, controllers, wsclients):
        import socket
        import tornado.ioloop
        import functools

        self._controllers = controllers
        self._wsclients = wsclients
        self.b = SDPReceiver(self._controllers)
        self.u = UDPComm(addr, port, self.b.datagram_from_controller)
        self.interval = 10
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.sync_tasks()

    def sync_tasks(self): # regular checks or tasks
        # put here tasks to be executed in regular intervals
        log.debug('Controllers:' + str(self._controllers))
        log.debug('WSClients:' + str(self._wsclients))
        self.ioloop.add_timeout(datetime.timedelta(seconds=self.interval), self.sync_tasks)

    def _callback(self, sock, fd, events):
        if events & self._io_loop.READ:
            self._callback_read(sock, fd)
        if events & self._io_loop.ERROR:
            print("IOLoop error")
            sys.exit(1)

    def _callback_read(self, sock, fd):
        (data, addr) = sock.recvfrom(4096)
        pass

class FileHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.render(args[0])



if __name__ == '__main__':
    from tornado.options import define, options, parse_command_line

    tornado.options.define("http_port", default = "8888", help = "HTTP port (0 to disable)", type = int)
    tornado.options.define("https_port", default = "4433", help = "HTTPS port (0 to disable)", type = int)
    tornado.options.define("listen_address", default = "0.0.0.0", help = "Listen this address only", type = str)
    tornado.options.define("udp_port", default = "44444", help = "UDP listen port", type = int)

    args = sys.argv
    args.append("--logging=debug")
    tornado.options.parse_command_line(args)

    controllers = Controllers()
    wsclients = WsClients()

    handler_settings = {
        "controllers": controllers,
        "wsclients": wsclients,
    }

    app_settings = {
        "debug": True
    }

    app = tornado.web.Application([
        (r'/files/(wstest.html|wstest.js)', FileHandler),
        (r'/api/v1/(servicegroups|hostgroups|services)(/(.*))?', RestHandler, handler_settings),
        (r'/api/v1/ws', WebSocketHandler, handler_settings),
        (r'/api/v1/', RootHandler),
        (r'/.*', UnknownHandler)
    ], **app_settings)

    if options.https_port != 0:
        print("HTTPS server listening on port " + str(options.https_port))
        import tornado.httpserver
        httpsserver = tornado.httpserver.HTTPServer(app, ssl_options = {
                "certfile": "receiver.itvilla.com.crt",
                "keyfile": "receiver.itvilla.com.key"
            })
        httpsserver.listen(options.https_port, address = options.listen_address)
        print("OK")

    if options.http_port != 0:
        print("HTTP server listening on port " + str(options.http_port))
        app.listen(options.http_port, address = options.listen_address)
        print("OK")

    UDPReader("0.0.0.0", int(options.udp_port), controllers, wsclients)

    import tornado.ioloop
    tornado.ioloop.IOLoop.instance().start()
