
# import sqlite3
# import re

# def _connect(dbfile):
#     conn = None
#     try:
#         conn = sqlite3.connect(dbfile)
#     except sqlite3.Error as e:
#         print("** ERROR: Failed to open DB '%s'" % e)
#     return conn

# def _execute(cursor, cmd, values=None):
#     try:
#         r = cursor.execute(cmd, values)
#     except sqlite3.Error as e:
#         print("** ERROR: failed to execute '%s' -- %s" % (cmd, e))

# def _executemany(cursor, cmd, valueList):
#     try:
#         r = cursor.executemany(cmd, valueList)
#     except sqlite3.Error as e:
#         print("** ERROR: failed to executemany '%s' -- %s" % (cmd, e))

# def _commit(conn):
#     try:
#         conn.commit()
#     except sqlite3.Error as e:
#         print("** ERROR: failed to commit '%s'" % e)

# _BOOK = 'IntradayBook'
# _TICK = 'Tickets'

# class StockDB:
#     def __init__(self, dbfile='data/sqlite.db'):
#         self._file = dbfile
#         # self._conn = _connect(dbfile)
#         # self._cur = self._conn.cursor()

#     # These functions should only run as beginning
#     def create_table(self):
#         _conn = _connect(self._file)
#         _cur = _conn.cursor()
#         _execute(_cur, """
#             CREATE TABLE IF NOT EXISTS %s (
#             id integer PRIMARY KEY,
#             ticket text NOT NULL,
#             date integer NOT NULL,
#             price integer NOT NULL,
#             isbuy integer NOT NULL,
#             vol integer NOT NULL,
#             totalVol integer,
#             totalVal integer,
#             FOREIGN KEY (ticket) REFERENCES %s(name)
#             );""" % (_BOOK, _TICK))
#         _execute(_cur, """
#             CREATE TABLE IF NOT EXISTS %s (
#             id integer PRIMARY KEY,
#             name text NOT NULL,
#             exchange text NOT NULL,
#             ssiref text,
#             );""" % _TICK)
#         _commit(_conn)
#         _conn.close()

#     def add_intraday(self, intra):
#         _conn = _connect(self._file)
#         _cur = _conn.cursor()
#         cmd = "INSERT INTO %s(ticket,date,price,isbuy,vol,totalVol,totalVal) VALUES(?,?,?,?,?,?,?)" % _BOOK
#         def intra_gen():
#             for k,v in intra.items():
#                 for i in v:
#                     date = int(re.findall(r'^/Date\((\d+)\)/', i['TradingDate'])[0])/1000
#                     data = (i['Stockcode'], date, i['Price'], i['IsBuy'],
#                             i['Vol'], i['TotalVol'], i['TotalVal'])
#                     yield data
#         _executemany(_cur, cmd, intra_gen())
#         _commit(_conn)
#         _conn.close()

#     def close(self):
#         # self._conn.close()
#         pass

import pandas as pd
import sqlite3
from datetime import datetime
import re, os, pickle, sqlite3
import pandas as pd

_DBFILE_ = 'data/stonk.db'

def getCursor():
    conn = sqlite3.connect(_DBFILE_)
    return conn.cursor()

def close(cur):
    cur.connection.close()

def initTable():
    conn = sqlite3.connect(_DBFILE_)
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS Intra (
            id integer PRIMARY KEY,
            ticket text NOT NULL,
            date integer NOT NULL,
            time integer,
            mp real NOT NULL,
            mv integer NOT NULL,
            mt integer NOT NULL,
            ov1 integer NOT NULL,
            ov2 integer NOT NULL,
            ov3 integer NOT NULL,
            op1 real NOT NULL,
            op2 real NOT NULL,
            op3 real NOT NULL,
            bv1 integer NOT NULL,
            bv2 integer NOT NULL,
            bv3 integer NOT NULL,
            bp1 real NOT NULL,
            bp2 real NOT NULL,
            bp3 real NOT NULL,
            buy integer NOT NULL
            );""")
    conn.commit()
    conn.close()

def saveIntra(ticket, intra, date, dbCursor=None):
    
    if dbCursor is None:
        conn = sqlite3.connect(_DBFILE_)
        cursor = conn.cursor()
    else:
        cursor = dbCursor
        
    date = int(date)

    def insert(items, exe=cursor.executemany):
        exe("""
        INSERT INTO Intra(ticket, date, time, mp, mv, mt,
                          ov1, ov2, ov3, op1, op2, op3,
                          bv1, bv2, bv3, bp1, bp2, bp3, buy)
                    VALUES(?, ?, ?, ?, ?, ?,
                          ?, ?, ?, ?, ?, ?,
                          ?, ?, ?, ?, ?, ?, ?)
        """, items)
    
    def intraGen():
        for i in range(len(intra)):
            x = intra.iloc[i]
            time = int(datetime.strptime('2000 '+x['time'], '%Y %H:%M:%S.%f').timestamp())
            yield [ticket, date, time, x['mp'], x['mv'], x['mt'],
                   x['ov1'], x['ov2'], x['ov3'], x['op1'], x['op2'], x['op3'],
                   x['bv1'], x['bv2'], x['bv3'], x['bp1'], x['bp2'], x['bp3'], int(x['buy'])]

    if intra is None:
        insert([ticket, date, None, 0, 0, 0, # A time=None indicate there's no Data available for this day
                0,0,0,0,0,0,
                0,0,0,0,0,0,0], exe=cursor.execute)
    else:
        insert(intraGen())
    
    if dbCursor is None:
        conn.commit()
        conn.close()

def convertIntra2sql():
    folderName = 'data/intras'
    
    initTable()
    conn = sqlite3.connect(_DBFILE_)
    cursor = conn.cursor()
    
    fnre = re.compile(r'^(...)_(........)\.pkl$')
    fileList = os.listdir(folderName)
    lastTicket = ''
    for fname in fileList:
        x = fnre.match(fname)
        if not x:
            continue
        ticket, date = x.groups()
        if ticket != lastTicket:
            print(ticket)
            lastTicket = ticket
        date = datetime.strptime(date + ' 07', '%Y%m%d %H').timestamp()
        intra = pickle.load(open(folderName+'/'+fname, 'rb'))

        saveIntra(ticket, intra, date, cursor)

    conn.commit()
    conn.close()

def getIntra(ticket, date, dbCursor=None):

    if dbCursor is None:
        conn = sqlite3.connect(_DBFILE_)
        # conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
    else:
        cursor = dbCursor

    cursor.execute("SELECT * FROM Intra WHERE ticket = '%s' AND date = %d" % (ticket, date))
    res = cursor.fetchall()
    if dbCursor is None:
        conn.close()

    if len(res) == 0:
        raise Exception('No entry found for "%s" on %d' % (ticket, date))
    if res[0][3] is None:
        return None
    df = pd.DataFrame(
        columns='date time mp mv mt ov1 ov2 ov3 op1 op2 op3 bv1 bv2 bv3 bp1 bp2 bp3 buy'.split(), 
        index=range(len(res)))
    for i in range(len(res)):
        x = res[i]
        df.at[i, 'date'] = x[2]
        df.at[i, 'time'] = x[3]
        df.at[i, 'mp'] = x[4]
        df.at[i, 'mv'] = x[5]
        df.at[i, 'mt'] = x[6]
        df.at[i, 'ov1'] = x[7]
        df.at[i, 'ov2'] = x[8]
        df.at[i, 'ov3'] = x[9]
        df.at[i, 'op1'] = x[10]
        df.at[i, 'op2'] = x[11]
        df.at[i, 'op3'] = x[12]
        df.at[i, 'bv1'] = x[13]
        df.at[i, 'bv2'] = x[14]
        df.at[i, 'bv3'] = x[15]
        df.at[i, 'bp1'] = x[16]
        df.at[i, 'bp2'] = x[17]
        df.at[i, 'bp3'] = x[18]
        df.at[i, 'buy'] = x[19]
    return df