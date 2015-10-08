import time
import socket
import tornado.ioloop
from functools import partial

from hosts import Hosts

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

MAX_RECV_BUF = 100000
MAX_SDP_SIZE = 5000

class UDPComm(object):
    ''' UDP socket listener '''
    def __init__(self, addr, port, handler, core):
        ''' Listen UDP socket and forward all incoming datagrams to
        the handler(host, data)

        :param addr: bind IP address ("0.0.0.0" for ANY)
        :param port: UDP listen port number
        :param handler: handler function for incoming data
        :param core: Core instance
        '''
        log.info('Initialise UDPComm(%s, %s, %s)', str(addr), str(port), str(handler))
        self.addr = addr
        self.port = port
        self._handler = handler
        self._core = core
        self._hosts = self._core.hosts()

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setblocking(False)
        self._sock.bind((self.addr, self.port))

        self._io_loop = tornado.ioloop.IOLoop.instance()
        self._io_loop.add_handler(self._sock.fileno(), partial(self._callback, self._sock), self._io_loop.READ)

    def _callback(self, sock, fd, events):
        ''' UDP socket event handler
        '''
        if events & self._io_loop.READ:
            self._callback_read(sock)
        if events & self._io_loop.ERROR:
            log.critical("IOLoop error")
            sys.exit(1)

    def _callback_read(self, sock):
        ''' UDP socket read event handler

        This method reads incoming UDP datagram, finds sender Host
        instance and calls self._handler with Host and datagram
        string (in UTF-8 encoding)

        :param sock: receiving socket instance

        '''
        (data, addr) = sock.recvfrom(MAX_RECV_BUF)
        if len(data) > MAX_SDP_SIZE:
            log.warning("datagram from %s is too big: %d", str(addr), len(data))
            return
        log.debug("got UDP datagram from %s @%.1f: %s", str(addr), time.time(), str(data))
        hosturi = 'udp://' + str(addr[0]) + ':' + str(addr[1])
        host = self._hosts.find_by_id(hosturi)
        host.set_receiver(self._handler)  # FIXME set it only once
        host.set_sender(self._send)  # FIXME set it only once
        host.set_addr(addr) # FIXME set it only once
        host.receiver(data)

    def _send(self, host, addr, sendstring):
        ''' Send UDP datagramm to the host

        id of host is (addr, port) duple. data can be binary data
        or string in UTF-8 encoding

        :param host: Host instance of controller
        :param addr: host (addr, port) tuple
        :param sendstring: string data to send
        '''
        if isinstance(sendstring, str):
            sendstring = sendstring.encode(encoding='UTF-8')
        log.info('send(%s, "%s")', str(host), sendstring)
        try:
            sendlen = self._sock.sendto(sendstring, addr)
            return sendlen
        except:
            import traceback
            traceback.print_exc() # debug
            return None

    def __str__(self):
        return('UDPComm(' + str(self.addr) + ':' + str(self.port) + '), known hosts:' + str(self._hosts))
