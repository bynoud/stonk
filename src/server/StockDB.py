
import sqlite3
import re

def _connect(dbfile):
    conn = None
    try:
        conn = sqlite3.connect(dbfile)
    except sqlite3.Error as e:
        print("** ERROR: Failed to open DB '%s'" % e)
    return conn

def _execute(cursor, cmd, values=None):
    try:
        r = cursor.execute(cmd, values)
    except sqlite3.Error as e:
        print("** ERROR: failed to execute '%s' -- %s" % (cmd, e))

def _executemany(cursor, cmd, valueList):
    try:
        r = cursor.executemany(cmd, valueList)
    except sqlite3.Error as e:
        print("** ERROR: failed to executemany '%s' -- %s" % (cmd, e))

def _commit(conn):
    try:
        conn.commit()
    except sqlite3.Error as e:
        print("** ERROR: failed to commit '%s'" % e)

_BOOK = 'IntradayBook'
_TICK = 'Tickets'

class StockDB:
    def __init__(self, dbfile='data/sqlite.db'):
        self._file = dbfile
        # self._conn = _connect(dbfile)
        # self._cur = self._conn.cursor()

    # These functions should only run as beginning
    def create_table(self):
        _conn = _connect(self._file)
        _cur = _conn.cursor()
        _execute(_cur, """
            CREATE TABLE IF NOT EXISTS %s (
            id integer PRIMARY KEY,
            ticket text NOT NULL,
            date integer NOT NULL,
            price integer NOT NULL,
            isbuy integer NOT NULL,
            vol integer NOT NULL,
            totalVol integer,
            totalVal integer,
            FOREIGN KEY (ticket) REFERENCES %s(name)
            );""" % (_BOOK, _TICK))
        _execute(_cur, """
            CREATE TABLE IF NOT EXISTS %s (
            id integer PRIMARY KEY,
            name text NOT NULL,
            exchange text NOT NULL,
            ssiref text,
            );""" % _TICK)
        _commit(_conn)
        _conn.close()

    def add_intraday(self, intra):
        _conn = _connect(self._file)
        _cur = _conn.cursor()
        cmd = "INSERT INTO %s(ticket,date,price,isbuy,vol,totalVol,totalVal) VALUES(?,?,?,?,?,?,?)" % _BOOK
        def intra_gen():
            for k,v in intra.items():
                for i in v:
                    date = int(re.findall(r'^/Date\((\d+)\)/', i['TradingDate'])[0])/1000
                    data = (i['Stockcode'], date, i['Price'], i['IsBuy'],
                            i['Vol'], i['TotalVol'], i['TotalVal'])
                    yield data
        _executemany(_cur, cmd, intra_gen())
        _commit(_conn)
        _conn.close()

    def close(self):
        # self._conn.close()
        pass
