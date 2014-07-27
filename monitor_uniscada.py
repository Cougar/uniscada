#!/usr/bin/python
# OOP ja tornado kasutusel udp sonumite vastuvotuks. vahenda sync osa , vt loppu
# neeme 20.07.2014 alustatud monitor_multi4.py alusel

import time
import datetime
from pytz import timezone
import pytz
utc = pytz.utc
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

from udpreader import *
from sdpbuffer import *

# Set the socket parameters for communication with the site controllers
SQLDIR='/srv/scada/uniscada/sqlite/' #  "/data/scada/sqlite" # testimiseks itvilla serveris
tables=['state','newstate','controller','commands','service_*'] # to be added
addr='0.0.0.0'
port = 44444 # testimiseks 44444, pane parast 44445
interval = 1

if len(sys.argv)>1: # port as parameter given
    port=int(sys.argv[1]) # otherwise default value set above will be used
    print('UDP port to listen set to', port)
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
        self.b = SDPBuffer(SQLDIR, tables) # data into state table and sending out from newstate
        self.u = UDPReader(self.addr, self.port, self.b.udp2state) # incoming data listening
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.interval = interval

    def sync_tasks(self,interval = 1): # regular checks or tasks
        print("executing sync tasks...")
        # put here tasks to be executed in 1 s interval
        sendqueue=(self.b.print_table('newstate')) # waiting data to be sent
        print('newstate queue',sendqueue)
        #if len(sendqueue) > 0:
            #sendstring=b.message2host()
            #u.udpsend(senstring)

        print("UPD processing until next sync...")
        self.ioloop.add_timeout(datetime.timedelta(seconds=interval), self.sync_tasks)


    def start(self):
        self.sync_tasks(self.interval)
        self.ioloop.start()


# ###############################################################

if __name__ == '__main__':

    m=MonitorUniscada(addr, port, SQLDIR, tables, interval)
    m.start()
