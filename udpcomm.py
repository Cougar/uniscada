import traceback
import socket
import tornado.ioloop
import functools # from functools import partial

from hosts import Hosts

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class UDPComm(object): # object on millegiparast vajalik
    '''
    listen and forward UDP messages
    '''
    def __init__(self, addr, port, handler):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setblocking(False)
        self._sock.bind((addr, port))

        self.addr=addr
        self.port=port
        self.handler=handler
        self._hosts = Hosts()

        self._io_loop = tornado.ioloop.IOLoop.instance()
        self._io_loop.add_handler(self._sock.fileno(), functools.partial(self._callback, self._sock), self._io_loop.READ)


    def _callback(self, sock, fd, events):  # fd is some file descriptor... (?)
        if events & self._io_loop.READ:
            self._callback_read(sock, fd)
        if events & self._io_loop.ERROR:
            log.critical("IOLoop error")
            sys.exit(1)

    def _callback_read(self, sock, fd):
        (data, addr) = sock.recvfrom(4096)
        log.debug("got UDP " + str({ "from": addr, "msg": str(data) }))
        host = self._hosts.find_by_id(addr)
        host.set_receiver(self._handler)  # FIXME set it only once
        host.set_sender(self.send)  # FIXME set it only once
        if not isinstance(data, str):
            data = data.decode("UTF-8")
        host.receiver(data)

    def send(self, host, sendstring = ''):
        '''
        actual udp sending. give message as parameter
        Sends UDP data immediately, adding self.inum if >0.
        '''
        if sendstring == '':
            log.info("send(): nothing to send!")
            return 0
        log.debug("send going to send to %s: %s", str(addr), sendstring)
        if isinstance(sendstring, str):
            sendstring = sendstring.encode(encoding='UTF-8')
        addr = host.get_id()
        try:
            sendlen = self._sock.sendto(sendstring, addr)
            log.debug('sent ack to '+str(repr(addr))+' '+str(sendstring).replace('\n',' '))
            return sendlen
        except:
            traceback.print_exc() # debug
            return None

# #############################################

if __name__ == '__main__':
    pass
