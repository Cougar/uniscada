''' Core system setup

This instance keeps pointers to all other core instances
that are needed for the whole system:

    UserSessions - authenticated users and their permission data
    Controllers - known controllers
    ServiceGroups - setup data for all service groups
    WsClients - list of active WebSocket connections
    MsgBus - global message bus for webscoket client live updates
    Hosts - all known controller connections

In addition of these instances, it also reads configuration
file and provides access to the configuration dictionary

This module has also wrapper for user authentication
'''

import configparser

from usersessions import UserSessions
from controllers import Controllers
from servicegroups import ServiceGroups
from wsclients import WsClients
from msgbus import MsgBus
from hosts import Hosts

from cookieauth import CookieAuth

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
        self._auth = CookieAuth()
        self._config = {}

    def read_config(self, configfile):
        ''' Read configuration file

        :param configfile: INI filename
        '''
        self._config = configparser.ConfigParser()
        self._config.read(configfile)

        self._config_cookieauth()

    def _config_cookieauth(self):
        config = self.config()
        if 'CookieAuth' in config:
            log.debug('CookieAuth setup')
            try:
                cookiename = config.get('CookieAuth', 'cookiename')
                dbhost = config.get('CookieAuth', 'dbhost')
                dbname = config.get('CookieAuth', 'dbname')
                dbuser = config.get('CookieAuth', 'dbuser')
                dbpass = config.get('CookieAuth', 'dbpass')
                self.auth().setup(cookiename, dbhost, dbuser, dbpass, dbname)
            except configparser.NoSectionError:
                log.error('CookieAuth section is missing in config file')
            except KeyError as e:
                log.error('no %s defined for CookieAuth in config file', str(e))
            except Exception as e:
                log.critical('config error: %s', str(e))
        else:
            log.warning('CookieAuth configuration missing')

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

    def config(self):
        ''' Get config dictionary

        :returns: config dictionary
        '''
        return self._config

    def auth(self):
        ''' Get Auth instance

        :returns: Auth instance
        '''
        return self._auth

    def __str__(self):
        return(str(self._id) + ': ' +
               'setup = ' + str(self._setup))

