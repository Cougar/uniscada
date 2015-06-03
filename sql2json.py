""" JSON dump of SQLite database

Input can be SQLite database file or SQLite dump text file

Output can be JSON string or JSON file(s)
"""

import sqlite3
import sys
import json

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())


class SQLdb(object):
    def __init__(self):
        log.info('Create SQLite dumper')
        self.conn = None

    def setconn(self, conn):
        """ Set SQLite connection

        :param conn: SQLite connection
        """
        self.conn = conn

    def loaddb(self, dbfilename):
        """ Connect to SQLite database

        :param dbfilename: SQLite database file name
        """
        try:
            conn = sqlite3.connect(dbfilename)
        except Exception as ex:
            log.critical('cant connect to SQLite db %s: %s', \
                dbfilename, str(sys.exc_info()[1]))
            raise Exception(ex)
        self.setconn(conn)

    def gettablelines(self, table):
        """ Get list of table line dictionaries

        :param table: table name
        :returns list of table line dictionaries
        """
        if not self.conn:
            log.critical('db is not connected')
            raise Exception()
        try:
            self.conn.row_factory = sqlite3.Row
            cur = self.conn.cursor()
            cur.execute('select * from %s' % table)
            for row in cur:
                yield dict(row)
        except Exception as ex:
            log.critical('cant read sql table %s: %s', \
                table, str(sys.exc_info()[1]))
            raise Exception(ex)

class SQLdump(object):
    def __init__(self, dumpfile):
        """ Read SQLite dump and create in-memory database

        :param dumpfile: SQLite dump file name
        """
        log.info('Load SQLite from dump file %s', dumpfile)
        self.conn = None
        try:
            sql = open(dumpfile, encoding='utf-8').read()
        except Exception as ex:
            log.critical('cant load SQLite dump from %s: %s', \
                dumpfile, str(sys.exc_info()[1]))
            raise Exception(ex)
        try:
            conn = sqlite3.connect(':memory:')
            conn.executescript(sql)
            conn.commit()
        except Exception as ex:
            log.critical('cant import SQLite dump %s: %s', \
                dumpfile, str(sys.exc_info()[1]))
            raise Exception(ex)
        self.conn = conn

    def getconn(self):
        """ Get SQLite connection

        :returns SQLite connection instance
        """
        return self.conn

class JSONdumper(object):
    def __init__(self):
        pass

    def dump(self, rows, field, value, dir, skipempty, skipfields, jsonmin, array, output):
        """ Dump database rows in JSON format

        :param rows: generator or database rows
        :param field: Field name for filename
        :param value: Dump only one row where field value matches
        :param dir: JSON dump direcory name
        :param skipempty: Do not dump empty fields
        :param skipfields: Comma separated field names to skip
        :param jsonmin: Minimal JSON format
        :param array: Display as JSON array
        :param output: Write ouptut to file
        """
        a = []
        for row in rows:
            if skipfields:
                for f in skipfields.split(','):
                    if not f in row:
                        log.warning('no such field in row: %s', f)
                    else:
                        del row[f]

            if skipempty:
                for k, v in list(row.items()):
                    if v == None:
                        del row[k]

            if value or dir:
                if not field in row:
                    log.critical('no such field in row: %s', field)
                    raise Exception

            if value and row[field] != value:
                continue

            if array:
                a.append(row)
            else:
                if jsonmin:
                    s = json.dumps(row)
                else:
                    s = json.dumps(row, indent=4, sort_keys=True)

                if dir:
                    print("WRITE: %s/%s" % (dir, row[field]))
                    with open("%s/%s" % (dir, row[field]), "w") as f:
                        f.write(s)
                else:
                    if output:
                        with open(output, "w") as f:
                            f.write(s)
                    else:
                        print(s)

        if array:
            if jsonmin:
                s = json.dumps(a)
            else:
                s = json.dumps(a, indent=4, sort_keys=True)
            if output:
                with open(output, "w") as f:
                    f.write(s)
            else:
                print(s)


if __name__ == '__main__':
    from tornado.options import define, options, parse_command_line

    define("db", default="", help="Database filename", type=str)
    define("dbdump", default="", help="Database dump filename", type=str)
    define("table", default="", help="Table name", type=str)
    define("field", default="", help="Field name for filename", type=str)
    define("value", default="", help="Dump only one row where field value matches", type=str)
    define("dir", default="", help="JSON dump direcory name", type=str)
    define("jsonmin", default=False, help="Minimal JSON format", type=bool)
    define("skipempty", default=False, help="Do not dump empty fields", type=bool)
    define("skipfields", default="", help="Comma separated field names to skip", type=str)
    define("array", default=False, help="Display as JSON array", type=bool)
    define("output", default="", help="Write ouptut to file", type=str)

    args = sys.argv
    args.append("--logging=error")
    parse_command_line(args)

    db = SQLdb()

    if options.db:
        db.loaddb(options.db)
    elif options.dbdump:
        db.setconn(SQLdump(options.dbdump).getconn())
    else:
        log.error('--db or --dbdump MUST BE set')
        sys.exit(1)

    if not options.table:
        log.error('--table MUST BE set')
        sys.exit(1)

    if options.value and not options.field:
        log.error('--field MUST BE set to use --value filter')
        sys.exit(1)

    if options.dir and not options.field:
        log.error('--field MUST BE set to dump into directory')
        sys.exit(1)

    if options.dir and options.array:
        log.error('--array CAN NOT be used with --dir')
        sys.exit(1)

    if options.dir and options.output:
        log.error('--output CAN NOT be used with --dir')
        sys.exit(1)

    JSONdumper().dump(db.gettablelines(options.table), options.field, options.value, options.dir, options.skipempty, options.skipfields, options.jsonmin, options.array, options.output)
