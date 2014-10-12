''' Physical host or device data structure for Comm module
'''

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'Host',
    'get_id',
    'set_sender',
    'send',
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
        log.debug('receiver(%s, "%s")', str(self._id), str(receivedmessage))
        self._receiver(self, receivedmessage)

    def send(self, sendmessage):
        ''' Send data to the host/controller

        This method is a wrapper for keeping all host/controller
        communication going via Host class for statistics purposes

        Data will sent by self._sender(self, sendmessage)

        :param sendmessage: data to send to the host/controller
        '''
        if not self._sender:
            log.error('send(%s, "%s"): callback not set', str(self._id), str(sendmessage))
            return
        log.debug('send(%s, "%s")', str(self._id), str(sendmessage))
        self._sender(self, sendmessage)

    def remove(self):
        ''' Remove this host instance from Hosts list '''
        if not self._listinstance:
            log.error('remove(%s): instance is not initiated by list', str(self))
            return
        else:
            log.info('remove(%s)', str(self))
            self._listinstance.remove_by_id(self.get_id())

    def __str__(self):
        return(str(self._id))
