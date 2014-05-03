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

import sqlite3
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


    def sqlread(self, filename): # drops table and reads from sql file filename that must exist
        table = str(filename.split('.')[0].split('/')[-1:])
        try:
            sql = open(filename, encoding="utf-8").read()
        except:
            raise SessionException('FAILURE in sqlread ' + filename + ': '+str(sys.exc_info()[1])) # aochannels ei pruugi olemas olla alati!

        Cmd='drop table if exists '+table
        try:
            self.conn.execute(Cmd) # drop the table if it exists
            self.conn.commit()
            self.conn.executescript(sql) # read table into database
            self.conn.commit()
        except:
            raise SessionException('sqlread: '+str(sys.exc_info()[1]))



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
        return self.buffer2json()

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
        cur=self.conn.cursor() # peaks olema soltumatu kursor
        sta_reg=''
        val_reg=''
        staTrue=False
        staExists=False
        valExists=False
        conv_coef=None
        key=''

        servicetable = ControllerData.get_servicetable(hid)
        Cmd="select sta_reg, val_reg,conv_coef from "+servicetable+" where sta_reg='"+register+"' or val_reg='"+register+"'"
        cur.execute(Cmd)
        for row in cur: # one row
            #svc_name=row[0]
            sta_reg=row[0]
            val_reg=row[1]
            conv_coef=eval(row[2]) if row[2] != '' else None

        if sta_reg !='': # sta_reg in use
            staExists=True
            if register == sta_reg:
                staTrue=True
            elif register == val_reg:
                staTrue=False
            key=val_reg # in most cases

        if val_reg !='': # val_reg exist
            valExists=True
            if register == sta_reg:
                staTrue=True
            elif register == val_reg:
                staTrue=False
            key=val_reg # in most cases

        return { 'key': key, 'staTrue': staTrue, 'staExists': staExists, 'valExists': valExists, 'conv_coef': conv_coef } # '',False,False,False if not defined in servicetable


    def init_userdata(self):
        userdata = NagiosUser(self.user).getuserdata()
        table = 'ws_hosts'

        ''' data from nagios put into tuple data
        [{u'saared': {u'alias': u'saared', u'members': {u'00204AB80BF9': u'saared tempa kanal'}}},
        {u'saared': {}, u'kvv': {u'00204AB80BF9': u'saared tempa kanal'}}}]
        Also adds servicegroup info from controllers. Does it gets dumped on each addcontroller?

        '''
        cur=self.conn.cursor()
        Cmd="BEGIN IMMEDIATE TRANSACTION"
        self.conn.execute(Cmd)
        # ws_hosts(hid,halias,ugid,ugalias,hgid,hgalias,cfg,servicegroup)
        usergroups = userdata.get('user_groups', {})
        for gid in usergroups.keys(): # access info usr_group alusel
            groupdata=usergroups[gid] #
            #galias=groupdata.get('alias') # seda ei ole esialgu user_group jaoks
            for hid in groupdata.keys():
                halias=groupdata.get(hid)
                Cmd="insert into "+table+"(hid,halias,ugid) values('"+hid+"','"+halias+"','"+gid+"')"
                #self.cmd=self.cmd+'\n'+Cmd # debug
                self.conn.execute(Cmd)

        hostgroups = userdata.get('hostgroups', {})
        for gid in hostgroups.keys(): # hostgroup kuuluvus  - neid voib olla rohkem kui neid millele on ligipaas. where filtreerib valja!
            groupdata=hostgroups.get(gid) # alias, members{}
            galias=groupdata.get('alias')
            members=groupdata.get('members') # hosts
            for hid in members.keys():
                servicetable = ControllerData.get_servicetable(hid)
                Cmd="update "+table+" set hgid='"+gid+"',hgalias='"+galias+"', servicegroup='"+servicetable+"' where hid='"+hid+"'"
                #print(Cmd) # debug
                self.conn.execute(Cmd)

        Cmd="select servicegroup from ws_hosts group by servicegroup" # open servicetables for service translations
        cur.execute(Cmd)
        servicetables = []
        for row in cur: # getting all used servicetables into memory
            servicetable=str(row[0])
            servicetables.append(str(row[0]))
        for servicetable in servicetables:
            self.sqlread('/srv/scada/sqlite/'+servicetable+'.sql')

        # controller and used servicetables must remain accessible in memory
        self.conn.commit()


    def state2state(self, host, age = 0): # updating state table in meory with the received udp data
        ''' copies all services for one host into the state copy in memory '''
        timefrom=0
        cur2=self.conn2.cursor()
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

        Cmd="BEGIN IMMEDIATE TRANSACTION"
        self.conn.execute(Cmd) # transaction begin
        for row in cur2:
            try:
                Cmd="insert into state(mac,register,value,timestamp) values('"+str(row[0])+"','"+str(row[1])+"','"+str(row[2])+"','"+str(row[3])+"')"
                #print(Cmd) # debug
                self.conn.execute(Cmd) #
            except:
                Cmd="UPDATE STATE SET value='"+str(row[2])+"',timestamp='"+str(row[3])+"' WHERE mac='"+row[0]+"' AND register='"+row[1]+"'"
                #print(Cmd) # debug
                self.conn.execute(Cmd) #
        self.conn.commit() # transaction end


    def state2buffer(self, host = '00204AA95C56', age = None): # esimene paring voiks olla 5 min vanuste kohta, hiljem vahem. 0 ei piira, annab koik!
        ''' Returns service refresh data as json in case of change or update from one host.
            With default ts_last all services are returned, with ts_last > 0 only those updated since then.
            Not needed after websocket is activated.
        '''
        timefrom=0
        cur=self.conn.cursor()
        self.ts = round(time.time(),1)
        if age == 0:
            timefrom = 0
        elif age >0:
            timefrom = self.ts - age
        else: # None korral arvestab eelmise lugemisega
            timefrom= self.ts
        #  servicebuffer(hid,svc_name,sta_reg,status INT,val_reg,value,timestamp NUMERIC) via conn
        Cmd="BEGIN IMMEDIATE TRANSACTION"
        self.conn.execute(Cmd) # transaction for servicebuffer

        Cmd="select mac,register,value,timestamp from state left join ws_hosts on state.mac=ws_hosts.hid where timestamp+0>"+str(timefrom)+" and mac='"+host+"'" # saame ainult lubatud hostidest
        cur.execute(Cmd)
        #self.conn.commit()
        for row in cur:
            hid=row[0]
            register=row[1]
            value=row[2]
            timestamp=row[3]
            #print('hid,register,value',hid,register,value) # debug

            regkey=self.reg2key(hid,register) # returns key,staTrue,staExists,valExists,conv_coef # all but first are True / False
            key=regkey['key']
            if regkey['staTrue'] == True: # status
                status=int(value) # replace value with status
                if regkey['valExists'] == False:
                    value=str(status)

            if regkey['staTrue'] == False: # value
                if regkey['staExists'] == False: # no status
                    status=0 # or -1?

            conv_coef=regkey['conv_coef']
            if key != '': # service defined in serviceregister
                try:
                    Cmd="insert into servicebuffer(hid,key,status,value,conv_coef,timestamp) values('"+hid+"','"+key+"','"+str(status)+"','"+value+"','"+str(conv_coef)+"','"+str(timestamp)+"')" # orig timestamp
                    #print(Cmd) # debug
                    self.conn.execute(Cmd)
                except:
                    #traceback.print_exc() # debug insert
                    #return 2 # debug
                    if regkey['staTrue'] == True: # status
                        Cmd="update servicebuffer set status='"+str(status)+"' where key='"+key+"' and hid='"+hid+"'" # no change to value
                    else: # must be value
                        Cmd="update servicebuffer set value='"+value+"' where key='"+key+"' and hid='"+hid+"'"
                    self.conn.execute(Cmd)
                #print(Cmd) # debug, what was selected

        self.conn.commit() # servicebuffer transaction end
        self.ts_last = self.ts
        return 0




    def buffer2json(self):
        '''  Returns json for service refresh in websocket client '''
        #servicebuffer(hid,key,status INT,value,timestamp NUMERIC)
        cur=self.conn.cursor()
        cur2=self.conn.cursor()
        Cmd="BEGIN IMMEDIATE TRANSACTION"
        self.conn.execute(Cmd) # transaction for servicebuffer
        Cmd="select hid from servicebuffer where status IS NOT NULL and value<>'' group by hid" # wait for for update
        cur.execute(Cmd)
        hid=''
        hid=''
        data=[] # tegelikult 1 host korraga
        hdata={}
        for row in cur: # hosts loop
            hid=row[0] # host id
            hdata={}
            hdata['host']=hid
            hdata['services']=[]
            hdata['timestamp']=self.ts # current time, not the time from hosts
            # servicebuffer(hid,svc_name,status INT,value,timestamp NUMERIC);
            Cmd="select * from servicebuffer where status IS NOT NULL and value<>'' and hid='"+hid+"'" #
            cur2.execute(Cmd)
            for row2 in cur2: # services loop
                key=row2[1]
                status=row2[2] # int
                value=row2[3] #
                conv_coef=row2[4] # num or none
                sdata={}
                sdata['key']=key
                sdata['status']=status
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
            #print('hdata: ',hdata) # debug
            data.append(hdata) # host ready


        Cmd="delete from servicebuffer where status IS NOT NULL and value<>''"
        self.conn.execute(Cmd)
        self.conn.commit()
        if len(data) == 0:
            return {}
        #print data # debug
        return data[0]


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

        s=Session(USER)

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

        # get user rights relative to the hosts
        # fill ws_hosts table and creates copies of servicetables in the memory
        s.init_userdata()

        # actual query execution
        result = s.sql2json(query, filter)

        # starting with http output
        http_status = 'Status: 200 OK'
        http_data = result

    except SessionAuthenticationError as e:
        http_status = 'Status: 307 Temporary Redirect'
        http_status += "\n" + 'Location: https://login.itvilla.com/login'
        http_status += "\n" + 'Set-Cookie: CookieAuth_Redirect=' + URL + '; Domain=.itvilla.com; Path=/'
        http_data['message'] = str(e);

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
