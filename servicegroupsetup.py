''' Initialize Servicegroup setup data structure from SQL dump
'''
import sqlite3
import sys

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'ServiceGroupSetup',
    'loadsql',
]

class ServiceGroupSetup(object):
    ''' Setup all services in one servicegroup '''
    def __init__(self, servicegroup, servicegroupname):
        ''' Prepare servicegroup setup import

        :param servicegroup: ServiceGroup instance
        :param servicegroupname: servicegroup name
        '''
        self._servicegroup = servicegroup
        self._servicegroupname = servicegroupname

    def loadsql(self, sqldir, field):
        ''' Create new servicegroup and update its setup from SQLite dump

        :param sqldir: directory of SQLite dump files
        :param field: service id field name
        '''
        log.info('Load servicegroup %s setup from SQLite dump', str(self._servicegroupname))
        sqldump = sqldir + self._servicegroupname + '.sql'
        try:
            sql = open(sqldump, encoding='utf-8').read()
        except Exception as e:
            log.critical('cant load sql dump from %s: %s', sqldump, str(sys.exc_info()[1]))
            raise Exception(e)

        try:
            conn = sqlite3.connect(':memory:')
            conn.executescript(sql)
            conn.commit()
        except Exception as e:
            log.critical('cant restore sql dump from %s: %s', sqldump, str(sys.exc_info()[1]))
            raise Exception(e)

        try:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute('select * from ' + self._servicegroupname)
            for row in cur:
                id = row[field]
                self._servicegroup._services.find_by_id(id).set_setup(dict(row))
        except Exception as e:
            log.critical('cant read sql table %s: %s', servicegroup, str(sys.exc_info()[1]))
            raise Exception(e)
