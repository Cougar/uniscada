''' Core system setup

This instance keeps pointers to all other core instances
that are needed for the whole system:

    UserSessions - authenticated users and their permission data
    Controllers - known controllers
    ServiceGroups - setup data for all service groups
    WsClients - list of active WebSocket connections
    MsgBus - global message bus for webscoket client live updates
    Hosts - all known controller connections
'''

from usersessions import UserSessions
from controllers import Controllers
from servicegroups import ServiceGroups
from wsclients import WsClients
from msgbus import MsgBus
from hosts import Hosts

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'Core',
]

class Core(object):
    def __init__(self):
        ''' Create new Core system instance
        '''
        log.debug('Create a new Core system instance')
        self._usersessions = UserSessions()
        self._wsclients = WsClients()
        self._msgbus = MsgBus()
        self._controllers = Controllers()
        self._servicegroups = ServiceGroups()
        self._hosts = Hosts()

    def save_state(self, statefile):
        ''' Save Controllers to statefile

        :param statefile: statefile name
        '''
        import pickle
        f = open(statefile, 'wb')
        pickler = pickle.Pickler(f, 0)
        pickler.dump(self._controllers)
        f.close()

    def restore_state(self, statefile):
        ''' Restore Controllers from statefile

        :param statefile: statefile name
        '''
        import pickle
        try:
            f = open(statefile, 'rb')
            log.info("restore state from pickle")
            unpickler = pickle.Unpickler(f)
            self._controllers = unpickler.load()
            log.info("controllers restored")
            f.close()
        except:
            log.info("cant restore controllers state")
            pass


    def usersessions(self):
        ''' Get UserSessions instance

        :returns: UserSessions instance
        '''
        return self._usersessions

    def wsclients(self):
        ''' Get WsClients instance

        :returns: WsClients instance
        '''
        return self._wsclients

    def msgbus(self):
        ''' Get MsgBus instance

        :returns: MsgBus instance
        '''
        return self._msgbus

    def controllers(self):
        ''' Get MsgBus instance

        :returns: MsgBus instance
        '''
        return self._controllers

    def servicegroups(self):
        ''' Get ServiceGroups instance

        :returns: ServiceGroups instance
        '''
        return self._servicegroups

    def hosts(self):
        ''' Get Hosts instance

        :returns: Hosts instance
        '''
        return self._hosts

    def __str__(self):
        return(str(self._id) + ': ' +
               'setup = ' + str(self._setup))

