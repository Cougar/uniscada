''' Controller setup data structure
'''
import sqlite3
import sys

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'ControllerSetup',
    'loadsql',
]

class ControllerSetup(object):
    ''' Setup all controllers '''
    def __init__(self):
        pass

    def loadsql(self, controllers, sqldump, table, field):
        ''' Read SQLite dump and update controller setups.
        Also create new controller instance if it is missing

        :param controllers: Controllers instance
        :param sqldump: SQLite dump
        :param table: SQLite table name
        :param field: SQLite table controler name field
        '''
        log.info('Load controller setup from SQlite dump %s table %s field %s', str(sqldump), str(table), str(field))
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
            cur.execute('select * from ' + table)
            for row in cur:
                id = row[field]
                controller = controllers.find_by_id(id)
                controller.set_setup(dict(row))
        except Exception as e:
            log.critical('cant read sql table %s: %s', table, str(sys.exc_info()[1]))
            raise Exception(e)
