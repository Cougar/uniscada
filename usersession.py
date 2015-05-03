''' User data structure
'''

from nagiosuser import NagiosUser

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'UserSession',
    'get_id',
    'get_userdata',
]

class UserSession(object):
    ''' One user '''
    def __init__(self, id, listinstance = None):
        ''' Create new user instance

        :param id: user id (username)
        :param listinstance: optional UserSessions instance
        '''
        log.debug('Create a new user (%s)', str(id))
        self._id = id
        self._isadmin = False
        self._isauthinprogress = False
        self._userdata = None
        self._userdata_callback = None
        self._controllerlist = {}
        self._servicegroupids = None

    def get_id(self):
        ''' Get id of user (username)

        :returns: user id (username)
        '''
        return self._id

    def read_userdata_form_nagois(self, callback = None):
        ''' Read userdata from Nagios

            Call callback() when response from Nagios is received

            :param callback: optional callback function
        '''
        if self._isauthinprogress:
            log.debug('Nagios auth already in progress')
            return
        self._isauthinprogress = True
        self._userdata_callback = callback
        try:
            NagiosUser().async_load_userdata(self._id, self._userdata_from_nagios)
        except Exception as e:
            log.error('Nagios check error')
            self._isauthinprogress = False
            raise e

    def _userdata_from_nagios(self, userdata):
        ''' Process Nagios reply with userdata

        After setting userdata, call _userdata_callback() if set

        :param userdata: userdata from Nagios
        '''
        if userdata:
            self._set_userdata(userdata)
        else:
            log.error('userdata missing')
        if self._userdata_callback:
            self._userdata_callback()
            self._userdata_callback = None
        self._isauthinprogress = False

    def _set_userdata(self, userdata):
        ''' Set userdata

        :param userdata: userdata
        '''
        try:
            if self._id != userdata.get('user_name', None):
                self._userdata = None
                log.error('Nagios didnt return right user data')
                raise Exception('Nagios didnt return right user data')
        except Exception as ex:
            self._userdata = None
            log.error('userdata check error: %s', str(ex))
            raise Exception('userdata check error: %s' % str(ex))
        self._userdata = userdata
        self._update_controllerlist()

    def _update_controllerlist(self):
        self._controllerlist = {}
        if not self._userdata:
            return
        if not 'user_groups' in self._userdata:
            log.warning('user %s does not have any user_groups defined', self._id)
            return
        for group in self._userdata.get('user_groups'):
            for mac in self._userdata.get('user_groups').get(group):
                self._controllerlist[mac] = True

    def set_servicegroupids(self, servicegroupids):
        self._servicegroupids = servicegroupids

    def get_servicegroupids(self):
        return self._servicegroupids

    def get_userdata(self):
        ''' Return userdata or None if not initialised

        :returns: userdata or None
        '''
        return self._userdata

    def set_admin(self):
        ''' Set admin privilege
        '''
        self._isadmin = True

    def is_admin(self):
        ''' Check if user has admin privilege

        :returns: True if user has admin privilege
        '''
        return self._isadmin

    def check_access(self, mac):
        ''' Check user access to the controller

        :param mac: mac address of controller

        :returns: True if access is granted, False otherwise
        '''
        if self.is_admin():
            return True
        if not self._userdata:
            return False
        if mac in self._controllerlist:
            return True
        return False

    def get_usersession_data_v1(self):
        ''' Get usersession data

        :returns usersession data
        '''
        return {
            "id": self._id,
            "admin": self._isadmin,
            "userdata": self._userdata,
            "controllerlist": self._controllerlist,
            "servicegroupids": self._servicegroupids,
            "authinprogress": self._isauthinprogress,
        }

    def __str__(self):
        return(str(self._id) + ': ' +
            'userdata = ' + str(self._userdata))
