''' Redis DB storage helper
'''
import redis
import json

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class Storage(object):
    ''' Redis helper '''
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._redis = None
        self._redis_connect()

    def exists(self, rkey):
        try:
            return self._redis.exists(rkey)
        except Exception as ex:
            log.warning('DEL(%s) error: %s', rkey, str(ex))
            return False

    def delete(self, rkey):
        try:
            self._redis.delete(rkey)
        except Exception as ex:
            log.warning('DEL(%s) error: %s', rkey, str(ex))

    def rename(self, rkey1, rkey2):
        try:
            self._redis.rename(rkey1, rkey2)
        except Exception as ex:
            log.warning('RENAME(%s, %) error: %s', rkey1, rkey2, str(ex))

    def hset(self, rhash, rfield, rval):
        try:
            self._redis.hset(rhash, rfield, rval)
        except Exception as ex:
            log.warning('HSET(%s, %s, %s) error: %s', rhash, rfield, rval, str(ex))

    def hset_data(self, rhash, rfield, data):
        rval = json.dumps(data)
        self.hset(rhash, rfield, rval)

    def hget(self, rhash, rfield):
        try:
            rval = self._redis.hget(rhash, rfield)
        except Exception as ex:
            log.warning('HGET(%s, %s) error: %s', rhash, rfield, str(ex))
            return None
        if rval:
            try:
                return rval.decode('utf8')
            except Exception as ex:
                log.error('hget utf8 decode(%s) error: %s', str(rval), str(ex))
                return

    def hget_data(self, rhash, rfield):
        rval = self.hget(rhash, rfield)
        if rval:
            return json.loads(rval)

    def hkeys(self, rkey):
        try:
            keys = self._redis.hkeys(rkey)
        except Exception as ex:
            log.warning('HKEYS(%s) error: %s', rkey, str(ex))
            return
        if not keys:
            return
        for key in keys:
            if key:
                yield key.decode('utf8')

    def sadd(self, rkey, rmember):
        try:
            if self._redis.sadd(rkey, rmember):
                log.debug('new set value')
        except Exception as ex:
            log.warning('SADD(%s, %s) error: %s', rkey, rmember, str(ex))
            self._redis_connect()

    def srem(self, rkey, rmember):
        try:
            if not self._redis.srem(rkey, rmember):
                log.debug('set %s key %s was missing', rkey, rmember)
        except Exception as ex:
            log.warning('SREM(%s, %s) error: %s', rkey, rmember, str(ex))
            self._redis_connect()

    def sismember(self, rkey, rmember):
        try:
            return self._redis.sismember(rkey, rmember)
        except Exception as ex:
            log.warning('SISMEMBER(%s, %s) error: %s', rkey, rmember, str(ex))
            self._redis_connect()
        return False

    def smembers(self, rkey):
        try:
            rmembers = self._redis.smembers(rkey)
        except Exception as ex:
            log.warning('SMEMBERS(%s) error: %s', rkey, str(ex))
            return
        if not rmembers:
            return
        for rmember in rmembers:
            try:
                yield rmember.decode('utf8')
            except Exception as ex:
                log.error('smembers utf8 decode(%s) error: %s', str(rval), str(ex))
                return

    def sscan_iter(self, rkey):
        try:
            for rval in self._redis.sscan_iter(rkey):
                yield rval.decode('utf8')
        except Exception as ex:
            log.warning('SSCAN(%s) iter error: %s', rkey, str(ex))

    def save_reg(self, controller, reg, val, ts):
        rhash = 'controller/' + controller + '/registers'
        rfield = reg
        rval = json.dumps({ "val": val, "ts": ts})
        log.debug('redis.HSET(%s,%s,%s)', rhash, rfield, rval)
        try:
            if self._redis.hset(rhash, rfield, rval):
                log.debug('new key')
        except Exception as ex:
            log.warning('reg HSET(%s, %s, %s) error: %s', rhash, rfield, rval, str(ex))

    def get_reg(self, controller, reg):
        """ Get reg from the state storage of this controller

        :param reg: register name

        :returns: register (value, timestamp) tuple or
        (None, None) if not exist
        """
        rhash = 'controller/' + controller + '/registers'
        rfield = reg
        try:
            rval = self._redis.hget(rhash, rfield)
        except Exception as ex:
            log.error('reg HGET(%s, %s) error: %s', rhash, rfield, str(ex))
            return (None, None)
        if rval == None:
            return (None, None)
        try:
            val = json.loads(rval.decode('utf8'))
        except Exception as ex:
            log.critical('reg HGET JSON.loads(%s) error: %s', str(rval), str(ex))
            return (None, None)
        return(val.get('val', None), val.get('ts', None))

    def get_all_reg(self, controller):
        """ Generates (reg, val, ts) tuples for all variables known
        for the controller

        :returns: Generated (reg, val, ts) tuple for each register
        """
        rhash = 'controller/' + controller + '/registers'
        try:
            for rkey, rval in self._redis.hscan_iter(rhash):
                reg = rkey.decode('utf8')
                try:
                    val = json.loads(rval.decode('utf8'))
                except Exception as ex:
                    log.critical('reg HSCAN JSON.loads(%s) error: %s', str(rval), str(ex))
                    return
                yield (reg, val.get('val', None), val.get('ts', None))
        except Exception as ex:
            log.warning('reg HSCAN(%s) ter error: %s', rhash, str(ex))
            return

    def _redis_connect(self):
        try:
            self._redis = redis.Redis(host=self._host, port=self._port,
                    db=self._db, password=self._password)
        except Exception as ex:
            log.error('Redis connection error: %s', str(ex))
