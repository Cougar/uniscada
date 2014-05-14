#!/usr/bin/python3
# -*- coding: utf_8 -*-
#
# 08.04.2014 kasutajale lubatud hostgruppide ja hostide mobiilsele kliendile raporteerimine. nagiose query, json.load test
# 12.04.2014 cougar tegi mitu parendust
# 13.04.2014 vaartuste ringiarvutamine vastavalt service_* conv_coef ning hex float voimalikkus. 2 mac piirang on veel sees !!!
# 14.04.2014 services value val masiivist member valja! alati []
# 16.04.2014 print("Access-Control-Allow-Origin: *") # mikk tahtis

DEBUG = True

''' USAGE

from monpanel import *
s=Session(USER) # instance tekitamine, teeb ka abitabeleid
s.init_userdata()
s.sql2json(query='servicegroups', filter ='')
s.sql2json(query='hostgroups', filter ='saared')
s.sql2json(query='servicegroup', filter ='service_pumplad4_ee')

s.state2buffer() # read state to find updates, temporary polling!!
s.buffer2json() # service update json ws kliendle

'''

import cgi, cgitb ,re # Import modules for CGI handling
#cgitb.enable()

import time
import traceback
import os
import sys
import requests  #  subprocess
import json
query=''

USER='' # sdmarianne' # :kvv6313    #  'sdtoomas'


class SessionException(Exception):
    def __init__(self, string):
        self.string = string
    def __str__(self):
        return 'Session Error: %s' % self.string

class SessionAuthenticationError(SessionException):
    def __init__(self, string=""):
        SessionException.__init__(self, string)


class TwoKeyBuffer:
    ''' buffer datasotre
    '''
    def __init__(self, buffer):
        self.buffer = buffer

    def insertdata(self, key1, key2, data):
        if not key1 in self.buffer:
            self.buffer[key1] = {}
        if key2 in self.buffer[key1]:
            raise Exception # data already in buffer
        self.buffer[key1][key2] = data

    def updatedata(self, key1, key2, datakey, dataval):
        if not key1 in self.buffer:
            raise Exception # no such key1
        if not key2 in self.buffer[key1]:
            raise Exception # no such key2
        self.buffer[key1][key2][datakey] = dataval

    def getdata(self, key1):
        if key1 in self.buffer:
            return self.buffer[key1]
        return {}

    def deletenotnull(self, key1):
        return
        if key1 in self.buffer:
            del self.buffer[key1]

class StateBuffer:
    '''  state buffer
    '''
    statebuffer = {}
    def __init__(self):
        pass
        # CREATE TABLE state(mac,register,value,timestamp, alarm, 'due_time');
        # CREATE UNIQUE INDEX macreg on state(mac,register);

    @staticmethod
    def insertdata(hid, register, data):
        TwoKeyBuffer(StateBuffer.statebuffer).insertdata(hid, register, data)

    @staticmethod
    def updatedata(hid, register, datakey, dataval):
        TwoKeyBuffer(StateBuffer.statebuffer).updatedata(hid, register, datakey, dataval)

    @staticmethod
    def getdata(hid):
        return TwoKeyBuffer(StateBuffer.statebuffer).getdata(hid)


class ServiceBuffer:
    ''' servicebuffer datasotre
    '''
    servicebuffer = {}
    def __init__(self):
        pass
        # CREATE TABLE servicebuffer(hid,key,status INT,value,conv_coef INT,timestamp NUMERIC);
        # CREATE UNIQUE INDEX hid_key_servicebuffer on 'servicebuffer'(hid,key)

    @staticmethod
    def insertdata(hid, key, data):
        TwoKeyBuffer(ServiceBuffer.servicebuffer).insertdata(hid, key, data)

    @staticmethod
    def updatedata(hid, key, datakey, dataval):
        TwoKeyBuffer(ServiceBuffer.servicebuffer).updatedata(hid, key, datakey, dataval)

    @staticmethod
    def getdata(hid):
        return TwoKeyBuffer(ServiceBuffer.servicebuffer).getdata(hid)

    @staticmethod
    def deletenotnull(hid):
        return
        TwoKeyBuffer(ServiceBuffer.servicebuffer).deletenotnull(hid)


class ServiceData:
    ''' servicegroup datastore
    '''
    servicedata = {}
    def __init__(self, servicegroup):
        self.servicegroup = servicegroup
        if servicegroup in self.__class__.servicedata:
            return
        self._loadsql()

    def _loadsql(self):
        ''' Load data from SQL file
        '''
        import sqlite3
        try:
            sql = open('/srv/scada/sqlite/' + self.servicegroup + '.sql', encoding="utf-8").read()
        except:
            print("ERROR: can't read sql /srv/scada/sqlite/" + self.servicegroup + ".sql: " + str(sys.exc_info()[1]))
            return
            raise SessionException('cant read servicegroup data for ' + self.servicegroup + ': ' + str(sys.exc_info()[1]))
        try:
            conn = sqlite3.connect(':memory:')
            conn.executescript(sql)
            conn.commit()
        except:
            raise SessionException('cant init servicegroup database: ' + str(sys.exc_info()[1]))
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute('select * from ' + self.servicegroup)
            self.__class__.servicedata[self.servicegroup] = {}
            self.__class__.servicedata[self.servicegroup]['sta_reg'] = {}
            self.__class__.servicedata[self.servicegroup]['val_reg'] = {}
            for row in cur:
                sta_reg = row['sta_reg']
                if sta_reg in self.__class__.servicedata[self.servicegroup]['sta_reg']:
                    raise SessionException('data for sta_reg "' + sta_reg + '" already exists')
                self.__class__.servicedata[self.servicegroup]['sta_reg'][sta_reg] = {}
                for key in row.keys():
                    self.__class__.servicedata[self.servicegroup]['sta_reg'][sta_reg][key] = row[key]
                val_reg = row['val_reg']
                if val_reg != None and val_reg != '':
                    if val_reg in self.__class__.servicedata[self.servicegroup]['val_reg']:
                        raise SessionException('data for val_reg "' + val_reg + '" already exists')
                    self.__class__.servicedata[self.servicegroup]['val_reg'][val_reg] = {}
                    for key in row.keys():
                        self.__class__.servicedata[self.servicegroup]['val_reg'][val_reg][key] = row[key]
        except:
            raise SessionException('cant read servicegroup database: ' + str(sys.exc_info()[1]))

    def getservicedata(self):
        ''' Return service data from cache

        :return: service data structure

        '''
        if self.servicegroup in self.__class__.servicedata:
            return self.__class__.servicedata[self.servicegroup]
        raise SessionException('servicegroup data missing')


class ControllerData:
    ''' Access to controller SQL data
        TODO:
            - expire/reload SQL
    '''
    controllercache = {}
    def __init__(self):
        ''' Load controller SQL to cache
        '''
        if len(self.__class__.controllercache) == 0:
            self._loadsql()

    def _loadsql(self):
        ''' Load data from SQL file
        '''
        import sqlite3
        try:
            sql = open('/srv/scada/sqlite/controller.sql', encoding="utf-8").read()
        except:
            raise SessionException('cant read controller data: ' + str(sys.exc_info()[1]))
        try:
            conn = sqlite3.connect(':memory:')
            conn.executescript(sql)
            conn.commit()
        except:
            raise SessionException('cant init controller database: ' + str(sys.exc_info()[1]))
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute('select * from controller')
            for row in cur:
                mac = row['mac']
                if mac in self.__class__.controllercache:
                    raise SessionException('data for this controller already exists')
                self.__class__.controllercache[mac] = {}
                for key in row.keys():
                    self.__class__.controllercache[mac][key] = row[key]
        except:
            raise SessionException('cant read controller database: ' + str(sys.exc_info()[1]))

    def __str__(self):
        return str(self.__class__.controllercache)

    @staticmethod
    def get_servicetable(mac):
        if mac in ControllerData.controllercache:
            return ControllerData.controllercache[mac]['servicetable']
        else:
            raise SessionException('no data for controller')


class NagiosUser:
    ''' Nagios data cache implementation
        TODO:
            - expire old entries
    '''
    baseurl = 'https://n.itvilla.com/get_user_data?user_name='
    nagiosdatacache = {}

    def __init__(self, user):
        ''' Load user data to the cache if missing

        :param user: user name

        '''
        if user == None:
            raise Exception('missing user')
        self.user = user
        if user in self.__class__.nagiosdatacache:
            return
        self._loaduserdata(user)

    def _loaduserdata(self, user):
        ''' Load user data from Nagios to the cache

        :param user: user name

        '''
        try:
            import requests
            nagiosdata = requests.get(self.__class__.baseurl + user).content.decode(encoding='UTF-8')
        except:
            raise SessionException('problem with nagios query: ' + str(sys.exc_info()[1]))
        try:
            jsondata = json.loads(nagiosdata)
        except:
            raise SessionException('problem with json: ' + str(sys.exc_info()[1]))
        try:
            if user != jsondata.get('user_data').get('user_name'):
                raise SessionException('invalid user name in nagios response')
        except:
            raise SessionException('invalid nagios response')
        self.__class__.nagiosdatacache[user] = jsondata.get('user_data')

    def getuserdata(self):
        ''' Return user data from cache

        :return: user data structure

        '''
        if self.user in self.__class__.nagiosdatacache:
            return self.__class__.nagiosdatacache[self.user]
        raise SessionException('user data missing')

    def __str__(self):
        return str(self.__class__.nagiosdatacache)


class APIUser:
    ''' API user data and permission checks
        TODO:
            - reload/expire old entries
    '''
    userdatacache = {}
    ''' user data cache structure:
        key1:
            username
        key2:
            nagiosdata - original data from NagiosUser
            hid - list of accessible host IDs
            servicegroups - list of servicegroups
            hostgroups - list of hostgroups
    '''

    def __init__(self, user):
        ''' Setup user data cache if empty

        :param user: user name

        '''
        if user == None or user == '':
            raise Exception('missing user')
        self.user = user
        if user in self.__class__.userdatacache:
            # user already known
            return
        self._loaduserdata()

    def _loaduserdata(self):
        ''' Load and setup user data cache
        '''
        userdata = {}
        nagios = NagiosUser(self.user)
        userdata['nagiosdata'] = nagios.getuserdata()

        userdata['hid'] = {}
        usergroups = userdata['nagiosdata'].get('user_groups', {})
        for gid in usergroups.keys(): # access info usr_group alusel
            groupdata = usergroups[gid]
            for hid in groupdata.keys():
                userdata['hid'][hid] = {}
                userdata['hid'][hid]['halias'] = groupdata.get(hid)
                userdata['hid'][hid]['gid'] = gid

        userdata['hostgroups'] = {}
        userdata['servicegroups'] = {}
        # add only hostgroups where accessible hosts exists
        for hostgroup in userdata['nagiosdata'].get('hostgroups', {}):
            if len(hostgroup) == 0:
                continue
            for host in userdata['nagiosdata']['hostgroups'][hostgroup].get('members', {}):
                if host in userdata['hid']:
                    if not hostgroup in userdata['hostgroups']:
                        userdata['hostgroups'][hostgroup] = {'alias': userdata['nagiosdata']['hostgroups'][hostgroup].get('alias', '')}
                    if not 'hosts' in userdata['hostgroups'][hostgroup]:
                        userdata['hostgroups'][hostgroup]['hosts'] = {}
                    userdata['hostgroups'][hostgroup]['hosts'][host] = {}
                    # add additional data from ControllerData for faster access
                    userdata['hostgroups'][hostgroup]['hosts'][host]['alias'] = userdata['nagiosdata']['hostgroups'][hostgroup]['members'][host]
                    servicegroup = ControllerData.get_servicetable(host)
                    userdata['hostgroups'][hostgroup]['hosts'][host]['servicegroup'] = servicegroup
                    userdata['servicegroups'][servicegroup] = True

        for servicegroup in userdata['servicegroups']: # getting all used servicetables into memory
            ServiceData(servicegroup)

        self.__class__.userdatacache[self.user] = userdata

    def getuserdata(self):
        ''' Return user data from cache

        :return: user data structure

        '''
        if self.user in self.__class__.userdatacache:
            return self.__class__.userdatacache[self.user]
        raise SessionException('user data missing')

    def check_hostgroup_access(self, hostgroup):
        userdata = self.getuserdata()
        if hostgroup in userdata.get('hostgroups', {}):
            return
        raise SessionException('no such hostgroup for this user')

    def check_host_access(self, hid):
        userdata = self.getuserdata()
        if hid in userdata.get('hid', {}):
            return
        raise SessionException('no such host for this user')

    def check_servicegroup_access(self, servicegroup):
        userdata = self.getuserdata()
        if servicegroup in userdata.get('servicegroups', {}):
            return
        raise SessionException('no such servicegroup for this user')

class Session:
    ''' This class handles data for mobile operator panel of the UniSCADA monitoring via websocket '''

    def __init__(self, user):
        self.user = user
        ControllerData() # copy of hosts configuration data into memory
        self.apiuser = APIUser(self.user)
        self.ts_last = 0 # last execution of state2buffer(), 0 means never

    def _hostgroups2json(self):
        hostgroups = []
        hostgroupdata = APIUser(self.user).getuserdata().get('hostgroups', {})
        for hostgroup in hostgroupdata:
            hostgroups.append({'hostgroup': hostgroup, 'alias': hostgroupdata[hostgroup].get('alias', '')})
        return hostgroups

    def _servicegroups2json(self):
        servicegroups = []
        for servicegroup in self.apiuser.getuserdata().get('servicegroups', {}):
            servicegroups.append({'servicegroup': servicegroup})
        return servicegroups

    def _hostgroup2json(self, filter):
        hostgroupdata = self.apiuser.getuserdata().get('hostgroups', {}).get(filter, {})
        hostgroup = { 'hostgroup': filter, 'hosts': [] }
        for host in hostgroupdata['hosts']:
            hostgroup['hosts'].append({ 'id': host, 'alias': hostgroupdata['hosts'].get(host, {}).get('alias', ''), 'servicegroup': hostgroupdata['hosts'].get(host, {}).get('servicegroup', '')})
        return hostgroup

    def _servicegroup2json(self, filter):
        sd = ServiceData(filter).getservicedata()['sta_reg']
        #(svc_name,sta_reg,val_reg,in_unit,out_unit,conv_coef,desc0,desc1,desc2,step,min_len,max_val,grp_value,multiperf,multivalue,multicfg)
        hgdata = { "servicegroup": filter, "services": [] }
        for sta_reg in sd:
            hdata={}
            hdata['svc_name']=sd[sta_reg]['svc_name']
            val_reg=sd[sta_reg]['val_reg']
            unit=sd[sta_reg]['out_unit']
            desc=[ sd[sta_reg]['desc0'], sd[sta_reg]['desc1'], sd[sta_reg]['desc2'] ]
            multiperf=sd[sta_reg]['multiperf']
            multivalue=sd[sta_reg]['multivalue'] # to be shown in the end of desc after colon
            try: # igas teenusetabelis ei ole esialgu seda tulpa
                multicfg=sd[sta_reg]['multicfg'] # configurable
            except:
                multicfg=''

            # key finding, depends.... svc_name can be used instead of key in fact.
            if ((val_reg[-1:] == 'V' or val_reg[-1:] == 'W') and sta_reg[-1:] =='S'): # single perf or multiperf service. must have sta_reg too.
                show=True
                key=val_reg
            elif (val_reg == '' and sta_reg[-1:] == 'S'): # status, single on/off, value will be the same as status for grapring via perf
                show=True
                key=sta_reg
            elif (val_reg != '' and sta_reg == ''): # no status, must be general setup variable or cmd, not related to service configuration
                show=False
                key=val_reg
            else:
                #print 'strange service',sta_reg,val_reg # debug
                key='' # '?'+sta_reg+val_reg+'?' # neid ei naita, kuna teenustetabelis defineerimata
                show=False

            if key != '': # skip if no key
                hdata['key']=key
                hdata['show']=show
                # members status and desc
                mperf=multiperf.split(' ')
                mvalue=multivalue.split(' ')
                #print 'key,mperf,mvalue',key,mperf,mvalue # debug

                hdata['description']=[]
                for dm in range(len(desc)): # desc0 desc1 desc2 processing ##############################################
                    desc_dm=''
                    description={}
                    description['status']=dm # 0 1 2

                    if (len(mvalue) > 0 and len(mperf) > 0): # there are members, some members to be shown too
                        if ':' in desc[dm]: # show values only if colon in desc
                            for m in range(len(mperf)):
                                if str(m+1) in mvalue:
                                    desc_dm=desc[dm]+' {{ '+mperf[m]+'.val }}'+unit
                    description['desc']=desc_dm
                    hdata['description'].append(description)

                hdata['multiperf']=[]
                for mp in range(len(mperf)): # multicfg processing #####################################################
                    multiperf={}
                    #multiperf['member']=mp+1 # 0+1... # jatame ara
                    if mperf[mp] == '': # saab olla ainult yheliikmelise teenuse puhul nii
                        multiperf['name']=hdata['svc_name']
                    else:
                        multiperf['name']=mperf[mp]
                    multiperf['cfg']=False
                    if (len(multicfg) > 0 and len(mperf) > 0): # there are members, some members are configurable too
                        if str(mp+1) in multicfg:
                            multiperf['cfg']=True
                    hdata['multiperf'].append(multiperf)

                hgdata['services'].append(hdata)

        return hgdata

    def _services2json(self, filter):
        self.state2state(host=filter, age=300)
        self.state2buffer(host=filter, age=300) # one host at the timestamp# age 0 korral koik mis leidub.
        return self.buffer2json(host=filter)

    def sql2json(self, query, filter):
        if query == 'hostgroups':
            if filter == None or filter == '':
                return self._hostgroups2json()
            else:
                self.apiuser.check_hostgroup_access(filter)
                return self._hostgroup2json(filter)

        if query == 'servicegroups':
            if filter == None or filter == '':
                return self._servicegroups2json()
            else:
                self.apiuser.check_servicegroup_access(filter)
                return self._servicegroup2json(filter)

        if query == 'services':
            if filter == None or filter == '':
                raise SessionException('missing parameter')
            else:
                self.apiuser.check_host_access(filter)
                return self._services2json(filter)

        raise SessionException('illegal query: ' + query)


    def reg2key(self,hid,register): # returns key,staTrue,staExists,valExists based on hid,register. do not start transaction or commit her!
        ''' Must be used for every service from every host, to use the correct key and recalculate numbers in values '''
        staTrue = False
        staExists = False
        valExists = False
        conv_coef = None
        key=''

        servicetable = ControllerData.get_servicetable(hid)
        sd = ServiceData(servicetable).getservicedata()

        if register in sd['val_reg'] and register in sd['sta_reg']:
            raise SessionException('both val_reg and sta_reg with the same key')

        if register in sd['sta_reg']:
            conv_coef = sd['sta_reg'][register].get('conv_coef', None)
            staExists = True
            staTrue = True
            key = register
            if sd['sta_reg'][register]['val_reg'] != '':
                valExists = True

        if register in sd['val_reg']:
            conv_coef = sd['val_reg'][register].get('conv_coef', None)
            valExists = True
            staTrue = False
            key = register
            if sd['val_reg'][register]['sta_reg'] != '':
                staExists = True

        return { 'key': key, 'staTrue': staTrue, 'staExists': staExists, 'valExists': valExists, 'conv_coef': conv_coef } # '',False,False,False if not defined in servicetable


    def state2state(self, host, age = 0): # updating state table in meory with the received udp data
        ''' copies all services for one host into the state copy in memory '''
        import sqlite3
        self.conn2 = sqlite3.connect('/srv/scada/sqlite/monitor') # ajutiselt, kuni midagi paremat tekib. state ja newstate tabelid
        cur2=self.conn2.cursor()
        timefrom=0
        self.ts = round(time.time(),1)
        if age == 0:
            timefrom = 0
        elif age >0:
            timefrom = self.ts - age
        else: # None korral arvestab eelmise lugemisega
            timefrom= self.ts
        Cmd2="select mac,register,value,timestamp from state where timestamp+0>"+str(timefrom)+" and mac='"+host+"'"
        cur2.execute(Cmd2)
        self.conn2.commit()
        for row in cur2:
            try:
                StateBuffer.insertdata(host, row[1], { 'value': row[2], 'timestamp': float(row[3]) })
            except:
                StateBuffer.updatedata(host, row[1], 'value', row[2])
                StateBuffer.updatedata(host, row[1], 'timestamp', float(row[3]))

    def state2buffer(self, host = '00204AA95C56', age = None): # esimene paring voiks olla 5 min vanuste kohta, hiljem vahem. 0 ei piira, annab koik!
        ''' Returns service refresh data as json in case of change or update from one host.
            With default ts_last all services are returned, with ts_last > 0 only those updated since then.
            Not needed after websocket is activated.
        '''
        timefrom=0
        self.ts = round(time.time(),1)
        if age == 0:
            timefrom = 0
        elif age >0:
            timefrom = self.ts - age
        else: # None korral arvestab eelmise lugemisega
            timefrom= self.ts

        state = StateBuffer.getdata(host)
        for register in state:
            if state[register]['timestamp'] <= timefrom:
                continue
            hid=host
            value=state[register]['value']
            status = 0
            timestamp=state[register]['timestamp']
            #print('hid,register,value',hid,register,value) # debug

            regkey=self.reg2key(hid,register) # returns key,staTrue,staExists,valExists,conv_coef # all but first are True / False
            key=regkey['key']
            if regkey['staTrue'] == True: # status
                try:
                    status=int(value) # replace value with status
                except:
                    # FIXME this should not happen!
                    print("ERROR: value=" + str(value))
                if regkey['valExists'] == False:
                    value=str(status)

            if regkey['staTrue'] == False: # value
                if regkey['staExists'] == False: # no status
                    status=0 # or -1?

            conv_coef=regkey['conv_coef']
            if key != '': # service defined in serviceregister
                try:
                    ServiceBuffer.insertdata(hid, key, { 'status': status, 'value': value, 'conv_coef': conv_coef, 'timestamp': timestamp})

                except:
                    #traceback.print_exc() # debug insert
                    #return 2 # debug
                    if regkey['staTrue'] == True: # status
                        ServiceBuffer.updatedata(hid, key, 'status', status)
                    else: # must be value
                        ServiceBuffer.updatedata(hid, key, 'value', value)

        self.ts_last = self.ts
        return 0




    def buffer2json(self, host):
        '''  Returns json for service refresh in websocket client '''
        hdata={}
        hdata['host'] = host
        hdata['services'] = []
        hdata['timestamp'] = round(time.time(),1) # current time, not the time from hosts
        buffdata = ServiceBuffer.getdata(host)
        for key in buffdata:
            value = buffdata[key]['value']
            conv_coef = buffdata[key]['conv_coef']
            sdata={}
            sdata['key'] = key
            sdata['status'] =buffdata[key]['status']
            sdata['value']=[]
            if key[-1:] == 'W':
                valmems=value.split(' ') # only if key ends with W
            else:
                valmems=[value] # single value

            for mnum in range(len(valmems)): # value member loop
                # {}
                #valmember['member']=mnum+1
                #valmember['val']=self.stringvalue2scale(valmems[mnum],conv_coef) # scale conversion and possible hex float decoding
                #sdata['value'].append(valmember) # member ready
                sdata['value'].append(self.stringvalue2scale(valmems[mnum],conv_coef))
            hdata['services'].append(sdata) # service ready
        ServiceBuffer.deletenotnull(host)
        return hdata


    def stringvalue2scale(self, input = '', coeff = None):
        ''' Accepts string as inputs, divides by conv_coef, returns string as output.
            Rounding in use based on conv_coef.
            Understands hex float strings and converts them to human readable form.
        '''
        if coeff != None and coeff != '':
            try:
                conv_coef = eval(coeff)
                if len(input)>10 and not ' ' in input and not '.' in input: # try hex2float conversion for long strings
                    input=self.floatfromfex(input) # kumulatiivne veekulu siemens magflow 16 char, key TOV
                output=str(round((eval(input)/conv_coef),2)) # 2kohta peale koma kui jagamistegur > 1
            except:
                output=input # ei konverteeri, endiselt string. kuidas aga hex float puhul?
        else:
            output=input # no conversion. '1' -> '1', 'text' -> 'text'

        return output


    def floatfromhex(self,input): # input in hex, output also string!
        try:
            a=int(input,16) # test if valid hex string on input
        except:
            return input # no conversion possible

        sign = int(input[0:2],16) & 128
        exponent = (int(input[0:3],16) & 2047)  - 1023
        if sign == 128:
            return str(float.fromhex('-0x1.'+input[3:16]+'p'+str(exponent))) # negatiivne
        return str(float.fromhex('0x1.'+input[3:16]+'p'+str(exponent))) # positiivne


# ##################### MAIN #############################



if __name__ == '__main__':

    BASE_URI = '/api/v1'
    COOKIEAUTH_DOMAIN = 'itvilla_com'

    USER = None

    URL = ''
    if 'HTTPS' in os.environ and os.environ['HTTPS'] == 'on':
        URL += 'https://' + os.environ.get('HTTP_HOST', 'localhost')
        port = os.environ.get('SERVER_PORT', '443')
        if port != '443':
            URL += ':' + port
    else:
        URL += 'http://' + os.environ.get('HTTP_HOST', 'localhost')
        port = os.environ.get('SERVER_PORT', '80')
        if port != '80':
            URL += ':' + port
    URL += os.environ.get('REQUEST_URI', '/')

    http_status = 'Status: 200 OK'
    http_data = {}

    try:

        try:
            # Python 2
            import Cookie
        except (NameError, ImportError):
            # Python 3
            import http.cookies as Cookie

        try:
            USER = Cookie.SimpleCookie(os.environ["HTTP_COOKIE"])[COOKIEAUTH_DOMAIN].value.split(':')[0]
        except (Cookie.CookieError, KeyError, IndexError):
            raise SessionAuthenticationError('not authenticated')

        if DEBUG:
            USER='sdmarianne'

        form = cgi.FieldStorage()
        query =  form.getvalue('query')
        filter = None

        if query == None:
            uri = os.environ.get('REQUEST_URI').replace(BASE_URI + '/', '').split('/')
            query = uri[0]
            if len(uri) > 1:
                filter = uri[1]

        if query == 'hostgroups':
            if filter == None:
                filter = form.getvalue('hostgroup')

        elif query == 'servicegroups':
            if filter == None:
                filter = form.getvalue('servicegroup')

        elif query == 'services':
            if filter == None:
                filter = form.getvalue('host')

        else:
            raise SessionException('unknown query')

        s = Session(USER)
        result = s.sql2json(query, filter)

        http_status = 'Status: 200 OK'
        http_data = result

    except SessionAuthenticationError as e:
        http_status = 'Status: 503 Service Unavailable'
        http_data['message'] = str(e);
        http_data['login_url'] = 'https://login.itvilla.com/login'

    except SessionException as e:
        http_status = 'Status: 500 Internal Server Error'
        http_data['message'] = str(e);

    finally:
        print(http_status)
        print("Content-type: application/json; charset=utf-8")
        print("Access-Control-Allow-Origin: *")
        if USER != None:
            print("X-Username: " + USER)
        print()
        print(json.dumps(http_data, indent = 4))
