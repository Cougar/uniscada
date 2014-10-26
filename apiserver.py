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
    http://receiver.itvilla.com:8888/api/v1/hosts/
    http://receiver.itvilla.com:8888/api/v1/hosts/00204AA95C56
    http://receiver.itvilla.com:8888/api/v1/controllers/
    http://receiver.itvilla.com:8888/api/v1/controllers/00204AA95C56

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
    https://receiver.itvilla.com:4433/api/v1/hosts/
    https://receiver.itvilla.com:4433/api/v1/hosts/00204AA95C56
    https://receiver.itvilla.com:4433/api/v1/controllers/
    https://receiver.itvilla.com:4433/api/v1/controllers/00204AA95C56

BAD
    http://receiver.itvilla.com:8888/
    http://receiver.itvilla.com:8888/api/v1/
    http://receiver.itvilla.com:8888/api/v1/hostgroups/x
    http://receiver.itvilla.com:8888/api/v1/hostgroups/itvilla
    http://receiver.itvilla.com:8888/api/v1/servicegroups/x
    http://receiver.itvilla.com:8888/api/v1/servicegroups/hvvmon_ee
    http://receiver.itvilla.com:8888/api/v1/services/x
    http://receiver.itvilla.com:8888/api/v1/services/0008E101A8E9
    http://receiver.itvilla.com:8888/api/v1/hosts/x
    http://receiver.itvilla.com:8888/api/v1/controllers/x

    https://receiver.itvilla.com:4433/
    https://receiver.itvilla.com:4433/api/v1/
    https://receiver.itvilla.com:4433/api/v1/hostgroups/x
    https://receiver.itvilla.com:4433/api/v1/hostgroups/itvilla
    https://receiver.itvilla.com:4433/api/v1/servicegroups/x
    https://receiver.itvilla.com:4433/api/v1/servicegroups/hvvmon_ee
    https://receiver.itvilla.com:4433/api/v1/services/x
    https://receiver.itvilla.com:4433/api/v1/services/0008E101A8E9
    https://receiver.itvilla.com:4433/api/v1/hosts/x
    https://receiver.itvilla.com:4433/api/v1/controllers/x

"""

# Too old distro (Red Hat Enterprise Linux Server release 6.2 (Santiago) / 6 December 2011)
import sys
sys.path.append('/root/tornado-3.2/')
sys.path.append('/root/backports.ssl_match_hostname-3.4.0.2/src')

import logging
import sys
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

import datetime

import json

import tornado.web
import tornado.gen

import signal

from udpcomm import *
from usersessions import UserSessions
from controllers import Controllers
from sdpreceiver import SDPReceiver
from wsclients import WsClients
from msgbus import MsgBus

from api import API

from cookieauth import CookieAuth
from roothandler import RootHandler
from filehandler import FileHandler
from resthandler import RestHandler
from unknownhandler import UnknownHandler
from websockethandler import WebSocketHandler

log = logging.getLogger(__name__)


class UDPReader(object):
    def __init__(self, addr, port, usersessions, controllers, wsclients, msgbus):
        import socket
        import tornado.ioloop
        import functools

        self._usersessions = usersessions
        self._controllers = controllers
        self._wsclients = wsclients
        self._msgbus = msgbus
        self.b = SDPReceiver(self._controllers, self._msgbus)
        self.u = UDPComm(addr, port, self.b.datagram_from_controller)
        self.interval = 10
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.sync_tasks()

    def sync_tasks(self): # regular checks or tasks
        # put here tasks to be executed in regular intervals
        log.debug('Users: %s', str(self._usersessions))
        log.debug('Controllers: %s', str(self._controllers))
        log.debug('WSClients: %s', str(self._wsclients))
        self.ioloop.add_timeout(datetime.timedelta(seconds=self.interval), self.sync_tasks)


is_closing = False

def signal_handler(signum, frame):
    global is_closing
    logging.info('exiting...')
    is_closing = True

def try_exit():
    global is_closing
    if is_closing:
        tornado.ioloop.IOLoop.instance().stop()
        logging.info('exit success')


if __name__ == '__main__':
    from tornado.options import define, options, parse_command_line

    tornado.options.define("http_port", default = "8888", help = "HTTP port (0 to disable)", type = int)
    tornado.options.define("https_port", default = "4433", help = "HTTPS port (0 to disable)", type = int)
    tornado.options.define("listen_address", default = "0.0.0.0", help = "Listen this address only", type = str)
    tornado.options.define("udp_port", default = "44444", help = "UDP listen port", type = int)
    tornado.options.define("statefile", default = "/tmp/apiserver.pkl", help = "Read/write server state to/from this file during statup/shutdown", type = str)

    args = sys.argv
    args.append("--logging=debug")
    tornado.options.parse_command_line(args)

    usersessions = UserSessions()
    wsclients = WsClients()
    msgbus = MsgBus()

    import pickle
    try:
        f = open(options.statefile, 'rb')
        log.info("restore state from pickle")
        unpickler = pickle.Unpickler(f)
        controllers = unpickler.load()
        log.info("controllers restored")
        f.close()
    except:
        controllers = Controllers()

    handler_settings = {
        "usersessions": usersessions,
        "controllers": controllers,
        "wsclients": wsclients,
        "msgbus": msgbus,
    }

    app_settings = {
        "debug": True
    }

    app = tornado.web.Application([
        (r'/files/(wstest.html|wstest.js)', FileHandler),
        (r'/api/v1/(servicegroups|hostgroups|services|hosts|controllers)(/(.*))?', RestHandler, handler_settings),
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

    UDPReader("0.0.0.0", int(options.udp_port), usersessions, controllers, wsclients, msgbus)

    import tornado.ioloop


    signal.signal(signal.SIGINT, signal_handler)
    tornado.ioloop.PeriodicCallback(try_exit, 100).start()
    tornado.ioloop.IOLoop.instance().start()

    log.info(' --- EXIT ---')

    import pickle
    f = open(options.statefile, 'wb')
    pickler = pickle.Pickler(f, 0)
    pickler.dump(controllers)
    f.close()
