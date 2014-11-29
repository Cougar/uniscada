'''
CookieAuth authentication module

MD5 based ticket-type user authentication

IP address cacheing and validation are not supported

Copyright (c) 2014 Droid4Control OÜ <cougar@droid4control.com>

This implementation is based on MOD_AUTH_COOKIE code CVS revision 1.7

This module has the same license that mod_auth_cookie.c

/* =======================================================================
 *       Copyright (c) 2004  Data Telecom, Ltd.
 *       All rights reserved.
 *       This software was written for Data Telecom Ltd. by Urmas Undusk
 *       and  is hereby contributed to the Apache Software Foundation for
 *       distribution under the Apache license, as follows.
 *
 *       Redistribution and use in source and binary forms, with or without
 *       modification, are permitted provided that the following conditions
 *       are met:
 *
 *       1. Redistributions of source code must retain the above copyright
 *               notice, this list of conditions and the following disclaimer.
 *
 *       2. Redistributions in binary form must reproduce the above copyright
 *               notice, this list of conditions and the following disclaimer in
 *               the documentation and/or other materials provided with the
 *               distribution.
 *
 *       3. All advertising materials mentioning features or use of this
 *               software must display the following acknowledgment:
 *               "This product includes software developed by the Apache Group
 *               for use in the Apache HTTP server project (http://www.apache.org/)."
 *
 *       4. The names "Apache Server" and "Apache Group" must not be used to
 *               endorse or promote products derived from this software without
 *               prior written permission. For written permission, please contact
 *               apache@apache.org.
 *
 *       5. Products derived from this software may not be called "Apache"
 *               nor may "Apache" appear in their names without prior written
 *               permission of the Apache Group.
 *
 *       6. Redistributions of any form whatsoever must retain the following
 *               acknowledgment:
 *               "This product includes software developed by the Apache Group
 *               for use in the Apache HTTP server project (http://www.apache.org/)."
 *
 *       THIS SOFTWARE IS PROVIDED BY THE APACHE GROUP `AS IS'' AND ANY
 *       EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 *       IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 *       PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE APACHE GROUP OR
 *       ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 *       SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
 *       NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 *       LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 *       HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 *       STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 *       ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 *       OF THE POSSIBILITY OF SUCH DAMAGE.
 * =======================================================================
 *
 *       This software consists of voluntary contributions made by many
 *       individuals on behalf of the Apache Group and was originally based
 *       on public domain software written at the National Center for
 *       Supercomputing Applications, University of Illinois, Urbana-Champaign.
 *       For more information on the Apache Group and the Apache HTTP server
 *       project, please see <http://www.apache.org/>.
 *
 * ======================================================================
'''
import pymysql
import hashlib
import time

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'CookieAuth',
]

class CookieAuth:
    def __init__(self):
        ''' CookieAuth authentication module '''
        self._conn = None
        self._secret_keys = {}

    def setup(self, cookiename, dbhost, dbuser, dbpass, dbname):
        ''' CookieAuth configuration setup

        :param cookiename: cookie name (CookieAuth_CookieName)
        :param dbhost: MySQL database server (CookieAuth_MySQL_Host)
        :param dbuser: MySQL username (CookieAuth_MySQL_User)
        :param dbpass: MySQL password (CookieAuth_MySQL_Passwd)
        :param dbname: MySQL database (CookieAuth_MySQL_DB)
        '''
        log.debug('setup(cookiename=%s, dbhost=%s, dbuser=%s, dbpass=*, dbname=%s)', cookiename, dbhost, dbuser, dbname)
        self._cookiename = cookiename
        self._dbhost = dbhost
        self._dbuser = dbuser
        self._dbpass = dbpass
        self._dbname = dbname

        self._connect_db()

    def get_user(self, cookiehandler):
        ''' Get authenticated username or None if missing

        cookiehandler(cookiename) should return cookie value or None

        :param cookiehandler: cookie read handler function
        :returns: authenticated username or None
        '''
        log.debug('get_user()')
        if not self._cookiename:
            log.error('cookiename is not set')
            return None
        cookie = cookiehandler(self._cookiename)
        if not cookie:
            log.info('cookie is missing')
            return None
        log.debug('get cookie: %s', cookie)
        if not self.check_cookie_md5(cookie):
            log.warning('MD5 error for cookie=%s', cookie)
            return None
        return cookie.split(':')[0]

    def _connect_db(self):
        ''' Create MySQL database connection

        If connection fails, self._conn is set to None and this will be retried next time again
        '''
        log.debug('_connect_db()')
        if self._conn:
            log.info('close old db connection')
            try:
                self._conn.close()
            except Exception as e:
                log.error('db connection close error: %s', str(e))
            finally:
                self._conn = None
        log.debug('connect to MySQL server "%s" database "%s" with user "%s"', self._dbhost, self._dbname, self._dbuser)
        try:
            self._conn = pymysql.connect(host=self._dbhost, port=3306, user=self._dbuser, passwd=self._dbpass, db=self._dbname)
        except Exception as e:
            log.critical('cant connect to database: ' + str(e))

    def _update_secret_keys(self):
        ''' Read valid secret keys from MySQL database '''
        log.debug('_update_secret_keys()')
        self._secret_keys = {}
        if not self._conn:
            log.warning('no db connection')
            return
        tm = int(time.time())
        cur = self._conn.cursor()
        try:
            cur.execute('SELECT version,secret_key,expire FROM secret_keys WHERE expire > ' + str(tm))
            for row in cur:
                log.debug('add secret_key version %d with expire %d', row[0], row[2])
                self._secret_keys[str(row[0])] = {
                        'version': row[0],
                        'secret_key': row[1],
                        'expire': row[2]
                    }
        except Exception as e:
            log.error('query error: %s', str(e))
            self._connect_db()
        finally:
            cur.close()

    def _expire_secrets(self):
        ''' Remove expired secret keys from the dictionary '''
        log.debug('expire_secrets()')
        tm = time.time()
        for version in self._secret_keys.keys():
            if self._secret_keys[version].get('expire', 9999999999) < tm:
                log.info('expire secret %s at %s', str(self._secret_keys[version]), str(tm))
                del(self._secret_keys[version])

    def _get_secret_key(self, version):
        ''' Get secret key based on version number

        :param version: secret key version (string)

        :returns: secret key or None
        '''
        log.debug('get_secret_key(%s)', version)
        self._expire_secrets()
        if not version in self._secret_keys:
            log.info('cached_secret_failed, checking db [key_version: %s]', str(version))
            self._update_secret_keys()
        if version in self._secret_keys:
            log.debug('got_cached_secret')
            return self._secret_keys[version].get('secret_key')
        log.error('no valid secret_key')
        return None

    def check_cookie_md5(self, cookie):
        ''' Check if CookieAuth cookie is valid or not

        Cookie value should be in format:
        <username>:<secret_key_version>:<md5>

        This method should never rais an excption but returns False
        in case of any error

        :param cookie: client cookie value

        :returns: True if cookie is valid, False when not
        '''
        log.debug('check_cookie_md5(%s)', str(cookie))
        try:
            (user, version, md5) = cookie.split(':', 3)
        except ValueError:
            log.error('cookie format error for "%s"', cookie)
            return False
        except AttributeError:
            log.error('cookie is not a string but %s', str(type(cookie)))
            return False
        log.debug('checking CookieAuth for user="%s", version="%s", md5="%s"', user, version, md5)
        secret_key = self._get_secret_key(version)
        if not secret_key:
            log.error('valid secret_key is missing')
            return False
        authmd5 = hashlib.md5((':'.join((user, version, secret_key))).encode(encoding='UTF-8')).hexdigest()
        log.debug('authmd5="%s"', authmd5)
        return authmd5 == md5
