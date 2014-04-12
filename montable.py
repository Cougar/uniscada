#!/usr/bin/python
# -*- coding: UTF-8 -*-# testime universaalset sisendinfopaneeli, mis oleks kiirem, kui nagios
# 03.01.2014 
# 9.10.2013
# 03.01.2014 kui olek on olemas, on ta enne value vaartust. sel juhul olekut ei naita, vaid varvime vaartuse rea vastavalt olekule roh koll pun
# 15.02.2014 nahtavale uuesti xxS teenused ja kogu asi ilusamaks

''' simple html table for fast viewing of monitoring data (Nagios is slow compared to this even with 3 s refresh rate!) '''


def output(register,value='puudub!',age=999,status=9): 
    """ Output html line with servicename, bg color depends on status """
    global maxage
    TR="<tr bgcolor='#cccccc'>" # html tag rea algusesse, varvi defineerimine, muudetakse statuse alusel
    Cmd2="select svc_name from "+servicetable+" where sta_reg = '"+register+"' or val_reg = '"+register+"'" # teenuse nimi leida
    cursor2.execute(Cmd2)
    servicename="<i>teenus defineerimata v&otilde;i seadistusmuutuja</i>" # juhuks, kui vastet ei leita
    for row2 in cursor2: # ainult yks rida vastuseks!
        servicename=row2[0]
        if status == 0: # ok
            TR="<tr bgcolor='#ccffcc'>" # taust roh, ok
            if len(value)>1: # perf, olgu veidi tumedam roheline
                TR="<tr bgcolor='#aaffaa'>" # taust roh, ok, perf mitte status
        elif status == 1: # warning
            TR="<tr bgcolor='#ffffcc'>" # taust koll, warning
            if len(value)>1: # perf, olgu veidi tumedam
                TR="<tr bgcolor='#ffffaa'>" #  perf mitte status
        elif status == 2: # critical
            TR="<tr bgcolor='#ffcccc'>" # taust pun, critical
            if len(value)>1: # perf, olgu veidi tumedam
                TR="<tr bgcolor='#ffaaaa'>" # perf mitte status
        else: 
            pass # jaab nagu enne oli
        
    if age>0.9*maxage: # hoiatame oranzi varviga, et selle info uuenemine on loppenud
        TR="<tr bgcolor='#F87217'>" # unkown, nagu nagioses, uuenemine lopenud. pumpkin orange
            
    statusrida=TR+"<td> "+servicename+" </td><td> "+register+" </td><td> "+value+" </td><td> "+str(age)+" </td></tr>\n"
    return statusrida
    


    
# ##################### MAIN #############################


# Import modules for CGI handling 
import cgi, cgitb ,re
cgitb.enable() 

from sqlite3 import dbapi2 as sqlite3 

import time
import datetime
from pytz import timezone
import pytz
utc = pytz.utc
import traceback
import os

tsnow = time.mktime(datetime.datetime.now().timetuple()) #sekundid praegu
age=0
age_meelde=0
register=''
register_meelde=''
lastperfregister=''
status=0
status_meelde=0
servicename=''
servicename_meeld=''
statusrida=''
statusrida_meelde=''
location = ''
mac=''
last=0 # viimase saatmise ts
perf=0

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
mac =  form.getvalue('mac')
if mac == None:
    print 'Error: no mac! </body></html>'
    exit()
    
maxage =  form.getvalue('maxage')
if maxage == None or maxage == '':
    maxage = 500 # s
else:
    maxage=int(float(maxage)) # numbriks

    
#env muutuja HTTP_COOKIE sisaldab kasulikku infot kui paring labi nagiose serveri teha. 
try:
    USER=os.environ['HTTP_COOKIE'].split(';')[2].split('=')[1].split(':')[0] # kasutajanime eraldamine jargmisest infost
    '''   # {'HTTP_COOKIE': '__utma=189087091.2060586936.1392656182.1392656182.1392656182.1; __utmz=189087091.1392656182.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); 
    itvilla_com=neeme:33:e14dba6b98611dc7ff225f01c9e1be8e; CookieAuth_Redirect=; 
    CookieAuth_Reason=', 'SERVER_SOFTWARE': 'Apache/2.2.23 (BaseN)', 'SCRIPT_NAME': '/conf/v1/montable.py', 'SERVER_SIGNATURE': '
Apache/2.2.23 (BaseN) Server at receiver.itvilla.com Port 80\n', 'REQUEST_METHOD': 'GET', 'SERVER_PROTOCOL': 'HTTP/1.1', 
'QUERY_STRING': 'mac=D05162F46081', 'PATH': '/sbin:/usr/sbin:/bin:/usr/bin', 
'HTTP_USER_AGENT': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.154 Safari/537.36', 'HTTP_CONNECTION': 'keep-alive', 'HTTP_REFERER': 'http://receiver.itvilla.com/conf/v1/montable.py?mac=D05162F46081', 'SERVER_NAME': 'receiver.itvilla.com', 'REMOTE_ADDR': '195.222.15.51', 'SERVER_PORT': '80', 'SERVER_ADDR': '46.183.73.35', 'DOCUMENT_ROOT': '/var/www/html', 'SCRIPT_FILENAME': '/var/www/v1/montable.py', 'SERVER_ADMIN': 'root@localhost', 'HTTP_HOST': 'receiver.itvilla.com', 'HTTP_CACHE_CONTROL': 'max-age=0', 'REQUEST_URI': '/conf/v1/montable.py?mac=D05162F46081', 'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'GATEWAY_INTERFACE': 'CGI/1.1', 'REMOTE_PORT': '4420', 'HTTP_ACCEPT_LANGUAGE': 'et-EE,et;q=0.8,en-US;q=0.6,en;q=0.4', 'HTTP_ACCEPT_ENCODING': 'gzip,deflate,sdch'}
'itvilla_com=neeme:27:f64d55b0f00b13446324e4e2af901fa8; CookieAuth_Redirect=; CookieAuth_Reason='

'''

except:
    print('error: no cookie')
    exit()
    
if USER == '' or USER == None:
    print 'Error: no username supplied! </body></html>'
    exit()

    
conn = sqlite3.connect('/srv/scada/sqlite/monitor')
cursor=conn.cursor()
cursor2=conn.cursor() # second connection to the same db

conn.execute('BEGIN IMMEDIATE TRANSACTION') # alustame transaktsiooni, peaks parem olema...

Cmd="select servicetable,location from controller where mac = '"+str(mac)+"'" # teenusetabel
cursor.execute(Cmd)
for row in cursor: # saame ainult yhe rea konkreetse mac kohta, tabelil unikaalne index
    servicetable=row[0]
    location=row[1]
    
# starting with html output
print "Content-type: text/html"
print 
print "<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd'>\n"
print "<html><head>\n"
print "<style media='screen' type='text/css'> body {background-color:#ffffff; font-family: arial; font-size: 75%; } table { font-family: arial;} </style>" 
print "<title>OlekuPaneel</title>\n"
print "<meta http-equiv='Content-Type' content='text/html; charset=utf-8'/>\n" # <meta http-equiv="refresh" content="1" />
print "<meta http-equiv='refresh' content='3'/>\n"  # 3s tagant automaatne reload #####
print "</head>\n<body>"
print "<h2> Monitooringusignaalid objektilt "+mac+"</h2>\n" 
print "<table border='5'>\n"  # paneeli algus
print "<tr bgcolor='#aaaaaa'><td colspan='4'>Kasutaja: "+USER+", objekt <b>"+location+"</b>, n&auml;idatava info max vanus: "+str(maxage)+"s </td></tr>" # esimene rida
print "<tr><th>J&auml;lgitava teenuse nimetus</th><th>Teenuse kood </th><th>Teenuse v&auml;&auml;rtusev&auml;lja sisu</th><th>Vanus s</th></tr>" # teine rida




Cmd="select register,value,timestamp from state where mac = '"+str(mac)+"' and timestamp+0>"+str(tsnow)+"-"+str(maxage)+" order by register" # find all fresh data for mac
cursor.execute(Cmd)
for row in cursor: #  monitooringusse saabunud key:val info hulgast selle maci varskem info. siin olek ja perfdata eraldi key-dega, lopp S voi V/W!
    if row[0]<>'' and row[2]<>None:
        register=row[0]
        value=row[1]
        last=int(float(row[2])) # leiame maksimumi koikide loetute hulgast
        age=int(round(tsnow - last))
        #print 'register,value,age',register,value,age,'<BR>' # debug
        
    if register[-1] == 'S': # status
        #print 'status ',register,value # debug
        #if register_meelde[:-1] != register[:-1]: # uus statusregister
        if lastperfregister[:-1] != register_meelde[:-1]: # peab eelmise ootel statuserea valjastama
            print(output(register_meelde,str(status_meelde),age_meelde,status_meelde)) # yksiku statusteenuse valjastamine (siin teenuses perfdata puudub)
        register_meelde=register
        status_meelde=status
        age_meelde=age
        status=int(float(value)) #
        status_meelde=status
        
    elif register[-1] == 'V' or register[-1] == 'W': # perfdata
        lastperfregister=register # tunnus et oli V voi W
        print(output(register,value,age,status_meelde))  # valjasta kohe meelesoleva staatusega
    else: 
        print(output(register,value,age)) # siin ei oska mingit statust anda
    
            
conn.commit() # end transaction

print "\n</table>\n<br>\n"  # lopetame tabeli
print "</body></html>\n"

