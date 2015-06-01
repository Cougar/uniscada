#!/usr/bin/python3

"""
Test URLs (default port, user=sdmarianne)

GOOD
    http://api.uniscada.eu/api/v1/hostgroups
    http://api.uniscada.eu/api/v1/hostgroups/
    http://api.uniscada.eu/api/v1/hostgroups/saared
    http://api.uniscada.eu/api/v1/servicegroups
    http://api.uniscada.eu/api/v1/servicegroups/
    http://api.uniscada.eu/api/v1/servicegroups/service_pumplad_ee
    http://api.uniscada.eu/api/v1/servicegroups/service_pumplad4_ee
    http://api.uniscada.eu/api/v1/services/00204AB80D57
    http://api.uniscada.eu/api/v1/services/00204AB80BF9
    http://api.uniscada.eu/api/v1/services/00204AA95C56
    http://api.uniscada.eu/api/v1/hosts/
    http://api.uniscada.eu/api/v1/hosts/00204AA95C56
    http://api.uniscada.eu/api/v1/controllers/
    http://api.uniscada.eu/api/v1/controllers/00204AA95C56

    https://api.uniscada.eu/api/v1/hostgroups
    https://api.uniscada.eu/api/v1/hostgroups/
    https://api.uniscada.eu/api/v1/hostgroups/saared
    https://api.uniscada.eu/api/v1/servicegroups
    https://api.uniscada.eu/api/v1/servicegroups/
    https://api.uniscada.eu/api/v1/servicegroups/service_pumplad_ee
    https://api.uniscada.eu/api/v1/servicegroups/service_pumplad4_ee
    https://api.uniscada.eu/api/v1/services/00204AB80D57
    https://api.uniscada.eu/api/v1/services/00204AB80BF9
    https://api.uniscada.eu/api/v1/services/00204AA95C56
    https://api.uniscada.eu/api/v1/hosts/
    https://api.uniscada.eu/api/v1/hosts/00204AA95C56
    https://api.uniscada.eu/api/v1/controllers/
    https://api.uniscada.eu/api/v1/controllers/00204AA95C56

BAD
    http://api.uniscada.eu/
    http://api.uniscada.eu/api/v1/
    http://api.uniscada.eu/api/v1/hostgroups/x
    http://api.uniscada.eu/api/v1/hostgroups/itvilla
    http://api.uniscada.eu/api/v1/servicegroups/x
    http://api.uniscada.eu/api/v1/servicegroups/hvvmon_ee
    http://api.uniscada.eu/api/v1/services/x
    http://api.uniscada.eu/api/v1/services/0008E101A8E9
    http://api.uniscada.eu/api/v1/hosts/x
    http://api.uniscada.eu/api/v1/controllers/x

    https://api.uniscada.eu/
    https://api.uniscada.eu/api/v1/
    https://api.uniscada.eu/api/v1/hostgroups/x
    https://api.uniscada.eu/api/v1/hostgroups/itvilla
    https://api.uniscada.eu/api/v1/servicegroups/x
    https://api.uniscada.eu/api/v1/servicegroups/hvvmon_ee
    https://api.uniscada.eu/api/v1/services/x
    https://api.uniscada.eu/api/v1/services/0008E101A8E9
    https://api.uniscada.eu/api/v1/hosts/x
    https://api.uniscada.eu/api/v1/controllers/x

"""

# Too old distro (Red Hat Enterprise Linux Server release 6.2 (Santiago) / 6 December 2011)
import sys
sys.path.append('/root/tornado-3.2/')
sys.path.append('/root/backports.ssl_match_hostname-3.4.0.2/src')

import logging
try:
    import chromalog
    chromalog.basicConfig(level=logging.DEBUG)
except Exception:
    pass
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

import datetime

import json

import tornado.web
import tornado.gen

import signal

from core import Core
from udpcomm import *
from sdpreceiver import SDPReceiver

from api import API

from cookieauth import CookieAuth
from roothandler import RootHandler
from filehandler import FileHandler
from resthandler import RestHandler
from unknownhandler import UnknownHandler
from websockethandler import WebSocketHandler

log = logging.getLogger(__name__)



class TimerTasks(object):
    def __init__(self, interval, core, udpcomm):
        import tornado.ioloop

        self._core = core
        self._udpcomm = udpcomm
        self._interval = interval
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self._timer_tasks()

    def _timer_tasks(self):
        ''' Tasks that needs to be executed in regular intervals '''
        log.debug('Users: %s', str(self._core.usersessions()))
        log.debug('Controllers: %s', str(self._core.controllers()))
        log.debug('Servicegroups: %s', str(self._core.servicegroups()))
        log.debug('WSClients: %s', str(self._core.wsclients()))
        log.debug('MsgBus: %s', str(self._core.msgbus()))
        log.debug('UDPComm: %s', str(self._udpcomm))
        self.ioloop.add_timeout(datetime.timedelta(seconds=self._interval), self._timer_tasks)

class UDPReader(object):
    def __init__(self, addr, port, core):
        import socket

        self._core = core
        self.b = SDPReceiver(self._core)
        self.u = UDPComm(addr, port, self.b.datagram_from_controller, self._core)

        TimerTasks(10, self._core, self.u)

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


    tornado.options.define("http_port", default = "80", help = "HTTP port (0 to disable)", type = int)
    tornado.options.define("https_port", default = "443", help = "HTTPS port (0 to disable)", type = int)
    tornado.options.define("listen_address", default = "0.0.0.0", help = "Listen this address only", type = str)
    tornado.options.define("udp_port", default = "44444", help = "UDP listen port", type = int)
    tornado.options.define("statefile", default = "/tmp/apiserver.pkl", help = "Read/write server state to/from this file during statup/shutdown", type = str)
    tornado.options.define("configfile", default = "./apiserver.ini", help = "Configuration file", type = str)

    args = sys.argv
    args.append("--logging=debug")
    tornado.options.parse_command_line(args)

    core = Core()
    core.read_config(options.configfile)

    core.restore_state(options.statefile)
    controllers = core.controllers()
    servicegroups = core.servicegroups()

    handler_settings = {
        "core": core,
    }

    app_settings = {
        "debug": True
    }

    app = tornado.web.Application([
        (r'/files/(wstest.html|wstest.js)', FileHandler),
        (r'/api/v1/(servicegroups|hostgroups|services|hosts|controllers|usersessions)(/(.*))?', RestHandler, handler_settings),
        (r'/api/v1/ws', WebSocketHandler, handler_settings),
        (r'/api/v1/', RootHandler),
        (r'/.*', UnknownHandler)
    ], **app_settings)

    if options.https_port != 0:
        print("HTTPS server listening on port " + str(options.https_port))
        import tornado.httpserver
        httpsserver = tornado.httpserver.HTTPServer(app, ssl_options = {
                "certfile": "api.uniscada.eu.crt",
                "keyfile": "api.uniscada.eu.key",
                "ca_certs": "COMODORSAAddTrustCA.crt"
            })
        httpsserver.listen(options.https_port, address = options.listen_address)
        print("OK")

    if options.http_port != 0:
        print("HTTP server listening on port " + str(options.http_port))
        app.listen(options.http_port, address = options.listen_address)
        print("OK")

    UDPReader("0.0.0.0", int(options.udp_port), core)

    import tornado.ioloop


    signal.signal(signal.SIGINT, signal_handler)
    tornado.ioloop.PeriodicCallback(try_exit, 100).start()
    tornado.ioloop.IOLoop.instance().start()

    log.info(' --- EXIT ---')

    core.save_state(options.statefile)
