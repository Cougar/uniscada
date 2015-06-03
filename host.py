''' Physical host or device data structure for Comm module
'''
from stats import Stats

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'Host',
    'get_id',
    'set_sender', 'set_addr',
    'send',
    'add_controller', 'del_controller', 'get_controller_list',
    'get_stats',
]

class Host(object):
    ''' One host/device '''
    def __init__(self, id, listinstance = None):
        ''' Create new host/device instance

        :param id: host/device id (IP, port duple)
        :param listinstance: optional Hosts instance
        '''
        log.info('Create a new host/device (%s)', str(id))
        self._id = id
        self._listinstance = listinstance
        self._receiver = None
        self._sender = None
        self._addr = None
        self._controllers = []
        self._stats = Stats()

    def get_id(self):
        ''' Get id of host/device (IP, port duple)

        :returns: id of host/device (IP, port duple)
        '''
        return self._id

    def set_receiver(self, receiver):
        ''' Set function for processing received data from the host/device

        :param receiver: pointer to receive(host, data) function
        '''
        log.debug('set_receiver(%s, %s)', str(self._id), str(receiver))
        self._receiver = receiver

    def set_sender(self, sender):
        ''' Set function for sending data back to the host/device

        :param sender: pointer to send(host, data) function
        '''
        log.debug('set_sender(%s, %s)', str(self._id), str(sender))
        self._sender = sender

    def set_addr(self, addr):
        ''' Set host/device address

        :param addr: host/device address
        '''
        log.debug('set_addr(%s, %s)', str(self._id), str(addr))
        self._addr = addr

    def receiver(self, receivedmessage):
        ''' Process data received from the host/controller

        This method is a wrapper for keeping all host/controller
        communication going via Host class for statistics purposes

        Data will be processed by self._receiver(self, receivedmessage)

        :param receivedmessage: data received from the host/controller
        '''
        if not self._receiver:
            log.error('receiver(%s, "%s"): callback not set', str(self._id), str(receivedmessage))
            return
        if not isinstance(receivedmessage, str):
            receivedmessage = receivedmessage.decode("UTF-8")
        log.debug('receiver(%s, "%s")', str(self._id), str(receivedmessage))
        self._stats.add('rx/bytes', len(receivedmessage))
        self._stats.add('rx/packets', 1)
        self._stats.set_timestamp('rx/last/timestamp')
        try:
            self._receiver(self, receivedmessage)
            self._stats.set('rx/last/datagram', receivedmessage)
        except Exception as e:
            self._stats.add('rx/errors', 1)
            self._stats.set('rx/last_error/datagram', receivedmessage)
            self._stats.set('rx/last_error/reason', str(e))
            self._stats.set_timestamp('rx/last_error/timestamp')

    def send(self, sendmessage):
        ''' Send data to the host/controller

        This method is a wrapper for keeping all host/controller
        communication going via Host class for statistics purposes

        Data will sent by self._sender(self, addr, sendmessage)

        :param sendmessage: data to send to the host/controller
        '''
        if not self._sender:
            log.error('send(%s, "%s"): callback not set', str(self._id), str(sendmessage))
            return
        log.debug('send(%s, %s, "%s")', str(self._id), str(self._addr), str(sendmessage))
        self._stats.add('tx/bytes', len(sendmessage))
        self._stats.add('tx/packets', 1)
        self._stats.set('tx/last/datagram', sendmessage)
        self._stats.set_timestamp('tx/last/timestamp')
        if isinstance(sendmessage, str):
            sendmessage = sendmessage.encode("UTF-8")
        self._sender(self, self._addr, sendmessage)

    def add_controller(self, controller):
        ''' Associate a new Controller with this Host

        This method associates Controller with this Host.

        :param controller: Controller to associate
        '''
        log.info('add_controller %d + 1: %s: %s', len(self._controllers), str(controller.get_id()), self.get_id())
        if controller in self._controllers:
            raise Exception('BUG: Controller ' + str(controller.get_id()) + ' is already associated with Host ' + str(self.get_id()))
        self._controllers.append(controller)

    def del_controller(self, controller):
        ''' Remove Controller association with this Host

        This method deassociates Controller from this Host. If there is
        no more controllers associated then Host instance will be
        removed from Hosts list.

        :param controller: Controller to deassociate
        '''
        log.info('del_controller %d - 1: %s: %s', len(self._controllers), str(controller.get_id()), self.get_id())
        if not controller in self._controllers:
            raise Exception('BUG: Controller ' + str(controller.get_id()) + ' is not associated associated with Host ' + str(self.get_id()))
        self._controllers.remove(controller)
        if not len(self._controllers):
            self._remove()

    def get_controller_list(self):
        ''' Generates a list of known controllers behind this host

        :returns: Generated controller item
        '''
        for controller in self._controllers:
            yield controller

    def _remove(self):
        ''' Remove this host instance from Hosts list '''
        if not self._listinstance:
            log.error('_remove(%s): instance is not initiated by list', str(self))
            return
        else:
            log.info('_remove(%s)', str(self))
            self._listinstance.remove_by_id(self.get_id())

    def get_stats(self):
        ''' Return some statistics

        :returns: statistics
        '''
        return self._stats.get()

    def __eq__(self, host):
        return self.get_id() == host.get_id()

    def __str__(self):
        return(str(self._id))
