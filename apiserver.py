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
import logging.config
try:
    import chromalog
except Exception:
    pass
from configparser import SafeConfigParser

import time
import datetime

import json

import ssl
import tornado.web
import tornado.gen

import signal
import re

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

is_closing = False
last_ctrlc = 0

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
        pass
        self.ioloop.add_timeout(datetime.timedelta(seconds=self._interval), self._timer_tasks)

class UDPReader(object):
    def __init__(self, addr, port, core):
        import socket

        self._core = core
        self.b = SDPReceiver(self._core)
        self.u = UDPComm(addr, port, self.b.datagram_from_controller, self._core)

        TimerTasks(10, self._core, self.u)

def signal_handler(signum, frame):
    global core
    global is_closing
    global last_ctrlc
    for key in dir(signal):
        sigval = getattr(signal, key)
        if isinstance(sigval, int) and sigval == signum and re.match(r'^SIG[A-Z]', key):
            log.info('signal: %s(%d)', key, signum)
    if signum == signal.SIGINT:
        t = time.time()
        if t < last_ctrlc + 1:
            log.info('exiting...')
            is_closing = True
        else:
            _statdump(core)
            log.info('press ^C once more within one sec to exit')
            last_ctrlc = t
    elif signum == signal.SIGUSR1:
        log.info('dump status...')
        _statdump(core)
    elif signum == signal.SIGTERM:
        log.info('exiting...')
        is_closing = True

def _statdump(core):
    status = logging.getLogger('status')
    status.info(' -------------------- dump status... --------------------')
    status.info('Users: %s', str(core.usersessions()))
    status.info('Controllers: %s', str(core.controllers()))
    status.info('Servicegroups: %s', str(core.servicegroups()))
    status.info('WSClients: %s', str(core.wsclients()))
    status.info('MsgBus: %s', str(core.msgbus()))
    status.info('UDPComm: %s', str(udpcomm.u))

def try_exit():
    global is_closing
    if is_closing:
        tornado.ioloop.IOLoop.instance().stop()
        logging.info('exit success')


if __name__ == '__main__':
    from tornado.options import define, options, parse_command_line

    logging.config.fileConfig('./apiserver.ini')
    mydefaultlevel = logging.getLogger().getEffectiveLevel()
    log.debug("log default logger lvl=%s, handlers=%s", logging.getLevelName(mydefaultlevel), str(logging.getLogger().handlers))
    for mylogger in logging.Logger.manager.loggerDict.keys():
        mylvl = logging.getLogger(mylogger).getEffectiveLevel()
        myhdl = logging.getLogger(mylogger).handlers
        if not mylvl == mydefaultlevel:
            log.info("log %s lvl=%s, handlers=%s", mylogger, logging.getLevelName(mylvl),  str(myhdl))

    for lvl in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        logging.log(getattr(logging, lvl), "test level %s", lvl)

    srvconfig = SafeConfigParser()
    srvconfig.read("./apiserver.ini")

    tornado.options.define("http_port", default = srvconfig.get('http', 'port', fallback=80), help = "HTTP port (0 to disable)", type = int)
    tornado.options.define("https_port", default = srvconfig.get('https', 'port', fallback=443), help = "HTTPS port (0 to disable)", type = int)
    tornado.options.define("certfile", default = srvconfig.get('https', 'certfile', fallback="apiserver.crt.pem"), help = "PEM certificate", type = str)
    tornado.options.define("keyfile", default = srvconfig.get('https', 'keyfile', fallback="apiserver.key.pem"), help = "PEM certificate key", type = str)
    tornado.options.define("ca_certs", default = srvconfig.get('https', 'ca_certs', fallback="cacert.pem"), help = "CA PEM certificate", type = str)
    tornado.options.define("listen_address", default = "0.0.0.0", help = "Listen this address only", type = str)
    tornado.options.define("udp_port", default = srvconfig.get('sdp', 'udp_port', fallback=44444), help = "UDP listen port", type = int)
    tornado.options.define("configfile", default = "./apiserver.ini", help = "Configuration file", type = str)

    args = sys.argv
    args.append("--logging=debug")
    tornado.options.parse_command_line(args)

    core = Core(configfile=options.configfile)

    controllers = core.controllers()
    servicegroups = core.servicegroups()

    handler_settings = {
        "core": core,
    }

    app_settings = {
        "debug": True
    }

    app = tornado.web.Application([
        (r'/files/([A-Za-z0-9\.\-_\/]+)', tornado.web.StaticFileHandler, {"path": "./static/"}),
        (r'/api/v1/(servicegroups|hostgroups|services|hosts|controllers|usersessions)(/(.*))?', RestHandler, handler_settings),
        (r'/api/v1/ws', WebSocketHandler, handler_settings),
        (r'/api/v1/', RootHandler),
        (r'/.*', UnknownHandler)
    ], **app_settings)

    if options.https_port != 0:
        log.info("HTTPS server listening on port %s", options.https_port)
        import tornado.httpserver
        httpsserver = tornado.httpserver.HTTPServer(app, ssl_options={
                "certfile": options.certfile,
                "keyfile": options.keyfile,
                "ca_certs": options.ca_certs,
                "ssl_version": ssl.PROTOCOL_TLSv1_2,
                "ciphers": (
                    'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:'
                    'DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:'
                    '!aNULL:!eNULL:!MD5:!RC4')
            })
        httpsserver.listen(options.https_port, address = options.listen_address)

    if options.http_port != 0:
        log.info("HTTP server listening on port %s", options.http_port)
        app.listen(options.http_port, address = options.listen_address)

    log.info("SDP listening on UDP port %s", options.udp_port)
    udpcomm = UDPReader("0.0.0.0", int(options.udp_port), core)

    import tornado.ioloop


    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGUSR1, signal_handler)
    signal.signal(signal.SIGALRM, signal_handler)
    tornado.ioloop.PeriodicCallback(try_exit, 100).start()
    tornado.ioloop.IOLoop.instance().start()

    log.info(' --- EXIT ---')
