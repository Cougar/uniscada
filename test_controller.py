#!/usr/bin/python3

CONTROLLER_ID = '000000000001'
CONTROLLER_SECRET = 'secret'
AGENT_IP = 'api.uniscada.eu'
AGENT_PORT = 44444

SIMULINTERVAL = 2000

MAXQUEUELEN = 100
MAXQUEUEAGE = 600
MAXSDPLEN = 1200

"""
                      +--------------------+
                      |                    |
                      |  SensorSimulator   +---+
                      |                    |   |
                      +--------------------+   |
                                               |
                          sdpqueue/append      |
                 +-----------------------------+
                 |
                 |    +--------------------+
                 +--->|                    |
                      |                    |
         +----------->|     SDPQueue       +---+
         |            |                    |   |
         |   +------->|                    |   |
         |   |        +--------------------+   |
         |   |                                 |
         |   |               sdp/out           |
         |   |   +-----------------------------+
         |   |   |
         |   |   |           sdp/ack
         +---|---|-----------------------------+
             |   |                             |
             |   |    +--------------------+   |
             |   +--->|                    +---+
             |        |                    |
         +---|------->|     SDPClient      +-------+
         |   |        |                    |       |
         |   o------->|                    +---+   |
         |   |        +--------------------+   |   |
         |   |                                 |   |
         |   |              sdp/nonce          |   |
         |   |   +-----------------------------+   |
         |   |   |                                 |
         |   |   |            nonce                |
         |   +---|-----------------------------+   |
         |       |                             |   |
         |       |    +--------------------+   |   |
         |       |    |                    |   |   |
         |       +--->|     SDPNonce       +---+   |
         |            |                    |       |
         |            +--------------------+       |
         |                                         |
         |                   udp/out               |
         |       +---------------------------------+
         |       |
         |       |
         |       |           udp/in
         +-------|-----------------------------+
                 |                             |
                 |    +--------------------+   |
                 |    |                    |   |
                 +--->|     UDPSocket      +---+
                      |                    |
                      +---------+----------+
                                |
                                |
                                V
                              Agent
"""

import sys
import time
import socket
import psutil

import tornado.ioloop
from functools import partial

import logging
try:
    sys.path.append('chromalog')
    import chromalog
    chromalog.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(name)s.%(module)s.%(funcName)s: %(message)s')
except Exception:
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

import zlib
import gzip

from sdp import SDP
from msgbus import MsgBus

from collections import deque

class UDPSocket(object):
    def __init__(self, msgbus, host, port):
        self._msgbus = msgbus
        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(0.1)
        self._io_loop = tornado.ioloop.IOLoop.instance()
        self._io_loop.add_handler(self._socket.fileno(), \
            partial(self._callback, self._socket), self._io_loop.READ)
        self._msgbus.subscribe(None, "udp/out", self, self._cb_udp_out)

    def _cb_udp_out(self, _token, _subject, message):
        datagram = message['value']
        log.debug('send to %s:%d:\n%s', self._host, self._port, str(datagram))
        datagram = datagram.encode('utf-8')
        datagram_zlib = zlib.compress(datagram, zlib.Z_BEST_COMPRESSION)
        datagram_gzip = gzip.compress(datagram)
        datagram_zlib2 = UDPSocket.compress(datagram)
        log.info("SIZE ASCII: %d, ZLIB: %d, GZIP: %d, ZLIB9: %d", \
            len(datagram), \
            len(datagram_zlib), \
            len(datagram_gzip), \
            len(datagram_zlib2))
        if len(datagram) > len(datagram_gzip):
            log.info('send ZIP')
            self._socket.sendto(datagram_gzip, (self._host, self._port))
            # self._socket.sendto(datagram_zlib, (self._host, self._port))
        else:
            self._socket.sendto(datagram, (self._host, self._port))

    def _callback(self, sock, fd, events):
        if events & self._io_loop.READ:
            self._callback_read(sock)
        if events & self._io_loop.ERROR:
            log.critical("IOLoop error")
            sys.exit(1)

    def _callback_read(self, sock):
        (data, addr) = sock.recvfrom(4096)
        data = data.decode('utf-8')
        log.debug("got UDP datagram from %s @%.1f:\n%s", \
            str(addr), time.time(), str(data))
        self._msgbus.publish("udp/in", {"value": data})

    @staticmethod
    def compress(buf):
        zdict = str.encode(u'\'}, {\', \': \'{}\', \'psversion\': \'\npsversion inid\', \'sha256\': \'SVW\n')
        compressor = zlib.compressobj(level=zlib.Z_BEST_COMPRESSION, zdict=zdict)
        result = compressor.compress(buf)
        return result + compressor.flush()


class SDPClient(object):
    def __init__(self, msgbus, controllerid, secretkey):
        self._msgbus = msgbus
        self._controllerid = controllerid
        self._secretkey = secretkey
        self._nonce = None
        self._msgbus.subscribe(None, "nonce", self, self._cb_nonce)
        self._msgbus.subscribe(None, "udp/in", self, self._cb_udp_in)
        self._msgbus.subscribe(None, "sdp/out", self, self._cb_sdp_out)
        self._msgbus.subscribe(None, "sdp/bootstrap", self, self._cb_sdp_bootstrap)

    def _cb_nonce(self, _token, _subject, message):
        self._nonce = message['value']

    def _cb_udp_in(self, _token, _subject, message):
        try:
            sdp = SDP.decode(message['value'])
        except Exception as ex:
            log.error('sdp.decode() exception: %s', str(ex))
        if not sdp.is_signed():
            log.error('datagram not signed')
            return
        if sdp.get_data('nonce'):
            self._msgbus.publish("sdp/nonce", {"value": sdp})
        else:
            self._msgbus.publish("sdp/ack", {"value": sdp})

    def _cb_sdp_out(self, _token, _subject, message):
        self._msgbus.publish("udp/out", message)

    def _cb_sdp_bootstrap(self, _token, _subject, _message):
        log.warning('_cb_sdp_bootstrap')
        self._inn = 999
        sdp = SDP(secret_key=self._secretkey, nonce='')
        sdp += ('id', self._controllerid)
        sdp += ('in', str(self._inn) + ',' + str(int(time.time())))
        datagram = sdp.encode()
        self._msgbus.publish("sdp/out", {"value": datagram})


class SDPNonce(object):
    def __init__(self, msgbus, secretkey):
        self._msgbus = msgbus
        self._secretkey = secretkey
        self._msgbus.subscribe(None, "sdp/nonce", self, self._cb_sdp_nonce)

    def _cb_sdp_nonce(self, _token, _subject, message):
        sdp = message['value']
        nonce = sdp.get_data('nonce')
        log.warning('nonce=%s', nonce)
        if nonce == None:
            return
        sdp.set_secret_key(self._secretkey)
        sdp.set_nonce(nonce)
        if not sdp.check_signature():
            log.error('signature error')
            return
        log.info('nonce replaced with: %s', str(nonce))
        self._msgbus.publish("nonce", {"value": nonce})


class SDPQueue(object):
    def __init__(self, msgbus, secretkey):
        self._msgbus = msgbus
        self._secretkey = secretkey
        self._nonce = None
        self._inn = 0
        self._queue = deque()
        self._msgbus.subscribe(None, "nonce", self, self._cb_nonce)
        self._msgbus.subscribe(None, "sdp/ack", self, self._cb_sdp_ack)
        self._msgbus.subscribe(None, "sdpqueue/append", self, self._cb_sdpqueue_append)

    def _cb_nonce(self, _token, _subject, message):
        self._nonce = message['value']
        self._process_queue()

    def _cb_sdpqueue_append(self, _token, _subject, message):
        if len(self._queue):
            log.warning('queue len: %d', len(self._queue))
        sdp = message['value']
        sdp.set_secret_key(self._secretkey)
        tm = int(time.time())
        sdp += ('in', str(self._inn) + ',' + str(tm))
        self._queue.append((sdp, self._inn, tm))
        self._inn += 1
        if len(self._queue) > MAXQUEUELEN:
            log.warning('queue overrun, remove oldest entry')
            self._queue.popleft()
        self._process_queue();

    def _queue_cleanup(self):
        now = time.time()
        while len(self._queue):
            [sdp_part, inn, tm] = self._queue[0]
            age = now - tm
            if age <= MAXQUEUEAGE:
                break
            log.debug('drop %s sec old entry %d from queue', int(age), inn)
            self._queue.popleft()

    def _process_queue(self):
        log.debug('queue len: %d', len(self._queue))
        if not len(self._queue):
            log.debug('queue is empty')
            return
        self._queue_cleanup()
        if not self._nonce:
            log.warning('nonce missing')
            self._msgbus.publish("sdp/bootstrap", None)
            return
        sdp = SDP(secret_key=self._secretkey, nonce=self._nonce)
        pos = 0
        datagram = None
        while pos < len(self._queue):
            [sdp_part, inn, tm] = self._queue[pos]
            controllerid = sdp_part.get_data('id')
            sdp += ('id', controllerid)
            sdp += sdp_part
            new_datagram = sdp.encode()
            if len(new_datagram) > MAXSDPLEN:
                log.info('more data than MAXSDPLEN, will send %d of %d items', pos, len(self._queue))
                self._msgbus.publish("sdp/out", {"value": datagram})
                return
            datagram = new_datagram
            pos += 1
        if datagram:
            self._msgbus.publish("sdp/out", {"value": datagram})

    def _cb_sdp_ack(self, _token, _subject, message):
        sdp = message['value']
        for part in sdp.gen_get():
            seq = part.get_in_seq()
            if seq != None:
                self._check_one_ack(seq)
        if len(self._queue):
            log.info('queue holds still %d items, will send more..', len(self._queue))
            self._process_queue()

    def _check_one_ack(self, seq):
        if not len(self._queue):
            log.error('got ACK %d but queue is empty', seq)
            return
        pos = 0
        inns = []
        while pos < len(self._queue):
            [sdp, inn, tm] = self._queue[pos]
            if inn != seq:
                inns.append(inn)
                pos += 1
                continue
            log.debug('got ACK, dequeue %d', inn)
            self._queue.popleft()
            if pos:
                log.warning('Removing SDPs older than ACK=%d: %s', inn, str(inns))
                while pos:
                    self._queue.popleft()
                    pos -= 1
            log.debug('queue len: %d', len(self._queue))
            return
        log.error('ACK for %s but no such SDP in queue', str(seq))

class SensorSimulator(object):
    def __init__(self, msgbus, controllerid):
        self._msgbus = msgbus
        self._controllerid = controllerid
        self._tmp_counter = 0

    def read_sensors(self):
        sdp = SDP()
        sdp += ('id', self._controllerid)
        sdp += ('psversion', psutil.__version__)
        sdp += ('emx', '')

        scputimes = psutil.cpu_times()
        sdp += ('CUV', getattr(scputimes, 'user'))
        sdp += ('CSV', getattr(scputimes, 'system'))
        sdp += ('CIV', getattr(scputimes, 'idle'))

        svmem = psutil.virtual_memory()
        sdp += ('MTV', getattr(svmem, 'total'))
        sdp += ('MAV', getattr(svmem, 'available'))
        sdp += ('MPV', getattr(svmem, 'percent'))
        sdp += ('MUV', getattr(svmem, 'used'))
        sdp += ('MFV', getattr(svmem, 'free'))
        sdp += ('MBV', getattr(svmem, 'buffers'))
        sdp += ('MCV', getattr(svmem, 'cached'))

        sdiskio = psutil.disk_io_counters()
        sdp += ('DRW', [ \
            getattr(sdiskio, 'read_count'), \
            getattr(sdiskio, 'read_bytes'), \
            getattr(sdiskio, 'read_time')])
        sdp += ('DWW', [ \
            getattr(sdiskio, 'write_count'), \
            getattr(sdiskio, 'write_bytes'), \
            getattr(sdiskio, 'write_time')])

        xxx = self._tmp_counter % 4
        sdp += ('xx'+str(xxx), str(getattr(scputimes, 'user')))
        sdp += ('CUS', xxx)
        if xxx == 1:
            sdp += ('xx0', '?')
        self._tmp_counter += 1
        self._msgbus.publish("sdpqueue/append", {"value": sdp})


if __name__ == '__main__':
    msgbus = MsgBus()
    UDPSocket(msgbus, host=AGENT_IP, port=AGENT_PORT)
    SDPNonce(msgbus, CONTROLLER_SECRET)
    SDPClient(msgbus, CONTROLLER_ID, CONTROLLER_SECRET)
    SDPQueue(msgbus, CONTROLLER_SECRET)
    simul = SensorSimulator(msgbus, controllerid=CONTROLLER_ID)
    tornado.ioloop.PeriodicCallback(simul.read_sensors, SIMULINTERVAL).start()
    tornado.ioloop.IOLoop.instance().start()
