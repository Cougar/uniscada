#!/usr/bin/python
# OOP ja tornado kasutusel udp sonumite vastuvotuks. vahenda sync osa , vt loppu
# neeme 20.07.2014 alustatud monitor_multi4.py alusel

import time
import datetime
#from pytz import timezone
#import pytz # py3?
#utc = pytz.utc # py3?
import sys
sys.path.append('/root/tornado-3.2/')
sys.path.append('/root/backports.ssl_match_hostname-3.4.0.2/src')
#import tornado

import traceback
#import subprocess

#from socket import *
import string

import tornado.ioloop
import functools

import logging
import sys
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
log = logging.getLogger(__name__)

from udpcomm import *
from controllers import Controllers
from sdpreceiver import SDPReceiver

# Set the socket parameters for communication with the site controllers
SQLDIR='/srv/scada/uniscada/sqlite/' #  "/data/scada/sqlite" # testimiseks itvilla serveris
tables=['state','newstate','controller','commands','service_*'] # to be added
addr='0.0.0.0'
port = 44442 # testimiseks, pane parast 44445
interval = 5 # effective for first only

if len(sys.argv)>1: # port as parameter given
    port=int(sys.argv[1]) # otherwise default value set above will be used
    log.info('UDP port to listen set to %d', port)
    sys.stdout.flush()


class MonitorUniscada:
    def __init__(self, addr, port, SQLDIR, tables, interval = 1):
        '''
        Listens incoming UDP from hosts with id, in SDP format, stores into sql buffer state.
        Sends ACK and possible commands or setup values back to the host (assuming the host
        socket has not been changed since last received UDP message from that host).
        '''

        self.addr = addr
        self.port = port
        self.SQLDIR = SQLDIR
        self.tables = tables # tuple
        self.c = Controllers()
        self.b = SDPReceiver(self.c)
        self.u = UDPComm(self.addr, self.port, self.b.datagram_from_controller) # incoming data listening
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.interval = interval

    def sync_tasks(self): # regular checks or tasks
        # put here tasks to be executed in regular intervals
        log.debug('Controllers:' + str(self.c))

        if interval > 0:
            #log.info("UPD processing until next sync...")
            self.ioloop.add_timeout(datetime.timedelta(seconds=self.interval), self.sync_tasks)


    def start(self):
        self.sync_tasks()
        self.ioloop.start()


# ###############################################################

if __name__ == '__main__':

    m=MonitorUniscada(addr, port, SQLDIR, tables, interval)
    m.start()
