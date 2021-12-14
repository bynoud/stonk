from flask import Flask, render_template, request, session, copy_current_request_context
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
import time, datetime, atexit, pickle
import pandas as pd
import numpy as np


from StrategySession import BacktestSession, Decision
from Symbol import SymbolHistory
import StockAPI, Statistics
import MoneyTrace

import pickle

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socket_ = SocketIO(app, async_mode=None, cors_allowed_origins='*')
thread = None
thread_lock = Lock()

def _fileload(fname, default=None):
    try:
        return pickle.load(open('./data/appdb/'+fname+'.pkl', 'rb'))
    except:
        return default
def _filesave(fname, db):
    try:
        pickle.dump(db, open('./data/appdb/'+fname+'.pkl', 'wb'))
    except Exception as e:
        print("Error during dump appdb: %s" % e)

class AppInf:
    def __init__(self) -> None:
        self.fav = _fileload('fav',[])
    
    def addFavorite(self, ticket):
        if ticket not in self.fav:
            self.fav.append(ticket)
            _filesave('fav', self.fav)
    
    def removeFavorite(self, ticket):
        if ticket in self.fav:
            self.fav.remove(ticket)
            _filesave('fav', self.fav)

    def toobject(self):
        return {'fav':self.fav}

db = {
    'sess': None,
    'updating': False,
}

appinf = AppInf()


def start_new_session(debug=False):
    if db['sess'] is not None:
        db['sess'].end()
    ss = BacktestSession(debug=debug)
    ss.start(lambda x: x.len>=200 and x.sma(src='volumn',window=90).iloc[-1]>100000)
    ss.get_signal_now()
    db['sess'] = ss
    print("New session is started %s @ %s" % (db, time.strftime("%A, %d. %B %Y %I:%M:%S %p")))

@app.route('/')
def index():
    print("HOMEE")
    return render_template('index.html', async_mode=socket_.async_mode)

#===========================================
# Socket
#===========================================
@socket_.on('my_event', namespace='/test')
def test_message(message):
    print("my_event %s", message)
    session['receive_count'] = session.get('receive_count',0) + 1
    emit('my_response', {'data':message['data'], 'count': session['receive_count']})

@socket_.on('my_broadcast_event', namespace='/test')
def test_broadcast_message(message):
    print("my_broadcast_event %s", message)
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socket_.on('disconnect_request', namespace='/test')
def disconnect_request():
    print("disconnect_request")
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)

def _ws_err(msg):
    emit('server_status',{'status':'bad', 'reason':msg})

@socket_.on('appdb', namespace='/test')
def appdb_wsreq(message):
    print("appdb_wsreq %s" % message)
    try:
        op = message['op']
        params = message['params']
        print("appdb %s %s" % (op, params))
        if op=='addFavorite':
            appinf.addFavorite(params['tic'])
        elif op=='delFavorite':
            appinf.removeFavorite(params['tic'])
        print("current fav %s" % appinf.fav)
        # return {'status':'ok', 'payload': appinf.fav}
        emit('appdb', appinf.toobject())
    except:
        _ws_err('appdb request failed')

@socket_.on('getGroups', namespace='/test')
def getGroupedTickets():
    try:
        prices = pickle.load(open('data/current_prices.pkl','rb'))
        tickets = list(prices.keys())
        groups = StockAPI.getIndustries(tickets)
        emit('ticketGroup', groups)
    except:
        _ws_err('getGroups failed')

#===========================================
@app.route('/debug-session')
def debug_session():
    start_new_session(True)
    return "A debug session is loaded"

@app.route('/renew-session')
def renew_session():
    start_new_session()
    return 'A new session is forced to renewed'

@app.route('/signal')
def signal():
    print("signal", db)
    if db['sess'] is None:
        return 'Session has not started yet'
    res = ''
    for tic,signals in db['sess'].signals.items():
        res += "<h>%s</h>" % tic
        for s in signals:
            if s['dec'] != Decision.KEEP:
                if type(s['reason']) is str:
                    res += "<p>%s : %s</p>" % (s['dec'], s['reason'])
                else:
                    res += "<p>%s</p>" % s['dec']
                    for reason in s['reason']:
                        res += "<li>%s</li>" % reason
                # res += "<p>[%s] %s : %s</p>" % (s['tic'], s['dec'], s['reason'])
    return res

@app.route('/resource', methods = ['POST'])
def testpost():
    print("%s : %s : %s" % (request.method, request.form, request.get_json()))
    # response = jsonify({'some': 'data'})
    # response.headers.add('Access-Control-Allow-Origin', '*')
    return {'some': 'data'}

# @app.route('/intra', methods = ['POST'])
# def getIntra():
#     params = request.get_json()
#     try:
#         ticket = params['tic']
#     except:
#         return {'status':'bad', 'reason':'No tic field is found'}
#     # try:
#     intra = Statistics.intraMatchedVol(ticket)
#     return {'status':'ok', 'payload':intra.to_dict(orient='records')}
#     # except Exception as e:
#     #     return {'status':'bad', 'reason': 'Failed to get intra "%s"' % e}

# @app.route('/today', methods = ['POST'])
# def getToday():
#     params = request.get_json()
#     try:
#         ticket = params['tic']
#     except:
#         return {'status':'bad', 'reason':'No tic field is found'}
#     # try:
#     intra = Statistics.intraMatchedVol2(ticket)
#     return {'status':'ok', 'payload':intra}
#     # except Exception as e:
#     #     return {'status':'bad', 'reason': 'Failed to get intra "%s"' % e}

@app.route('/daily', methods = ['POST'])
def getDaily():
    params = request.get_json()
    try:
        ticket = params['tic']
    except:
        return {'status':'bad', 'reason':'No tic field is found'}
    try:
        sym = pickle.load(open('data/tmp_symbol_%s.pkl' % ticket, 'rb'))
    except:
        sym = SymbolHistory(ticket, StockAPI.getPriceHistory(ticket, 365*2+50))
        pickle.dump(sym, open('data/tmp_symbol_%s.pkl' % ticket, 'wb'))
    # try:
    daily = Statistics.dailyStat(sym).fillna(0).round(2)
    return {'status':'ok', 'payload': daily.to_dict(orient='records')}
    # except Exception as e:
    #     return {'status':'bad', 'reason':'Failed %s'%e}

@app.route('/today-test', methods = ['POST'])
def getTodayTest():
    params = request.get_json()
    try:
        ticket = params['tic']
    except:
        return {'status':'bad', 'reason':'No tic field is found'}
    try:
        price = pickle.load(open('data/tmp_price_%s.pkl' % ticket, 'rb'))
    except:
        # sym = SymbolHistory(ticket, StockAPI.getPriceHistory(ticket, 365*2+50))
        price = StockAPI.getPriceHistory(ticket, 200)
        pickle.dump(price, open('data/tmp_price_%s.pkl' % ticket, 'wb'))
    sym = SymbolHistory(ticket, price=price)
    df = pd.DataFrame(sym.ohcl)
    df['volumn'] = sym.volumn
    df['time'] = sym.time

    avg = df.close.rolling(window=10).mean()
    pf = Statistics.polyfit(df.close, 1, errAccept=0.008, avg=avg)
    pf2 = Statistics.polyfit(df.close, 2, errAccept=0.01, avg=avg)
    df['fitval'] = pf.fitval
    df['fitCurve'] = pf2.fitval

    daily = Statistics.dailyStat(sym)
    df['volRsi'] = daily.volRsi
    df['buyVol'] = daily.buyVol
    df['sellVol'] = daily.sellVol
    df['unkVol'] = df.volumn - daily.sellVol - daily.buyVol
    df['unkVol'][df.unkVol.isnull()] = df.volumn

    df = df.replace({np.nan:None})
    return {'status':'ok', 'payload': df.to_dict(orient='records')}

@app.route('/abv-test', methods = ['POST'])
def getAbvTest(tillDate=1):
    params = request.get_json()
    try:
        ticket = params['tic']
    except:
        return {'status':'bad', 'reason':'No tic field is found'}
    # try:
    #     price = pickle.load(open('data/tmp_price_%s.pkl' % ticket, 'rb'))
    # except:
    #     # sym = SymbolHistory(ticket, StockAPI.getPriceHistory(ticket, 365*2+50))
    #     price = StockAPI.getPriceHistory(ticket, 200)
    #     pickle.dump(price, open('data/tmp_price_%s.pkl' % ticket, 'wb'))
    df = MoneyTrace.abvRsi(ticket, tillDate=tillDate)
    df['volRsi'] = df.abvRsi
    abvSum = df.buyVol + df.sellVol
    df['buyVol'] = df.buyVol * df.volumn / abvSum
    df['sellVol'] = df.sellVol * df.volumn / abvSum
    df['unkVol'] = df.volumn - df.sellVol - df.buyVol

    df = df.replace({np.nan:None})
    return {'status':'ok', 'payload': df.to_dict(orient='records')}

@app.route('/grouped-tickets', methods=['POST'])
def getGroupedTickets():
    prices = pickle.load(open('data/current_prices.pkl','rb'))
    tickets = list(prices.keys())
    groups = StockAPI.getIndustries(tickets)
    return {'status':'ok','payload':groups}

@app.route('/appdb', methods=['POST'])
def favoriteTicket():
    params = request.get_json()
    try:
        op = params['op']
        otherparam = params['params']
        print("appdb %s %s" % (op, otherparam))
        if op=='addFavorite':
            appinf.addFavorite(params['tic'])
        elif op=='delFavorite':
            appinf.removeFavorite(params['tic'])
        print("current fav %s" % appinf.fav)
        return {'status':'ok', 'payload': appinf.fav}
    except:
        return {'status':'bad', 'reason':'Wrong param'}

@app.route('/update-intra', methods=['POST'])
def updateIntra():
    if db['updating']:
        return {'status':'warn', 'reason':'The database is updating'}

    params = request.get_json()
    try:
        tillDate = params['tillDate']
        refetch = params['refetch']
        print("update-intra %s %s" % (tillDate, refetch))
        if refetch:
            MoneyTrace.ticketFilter()
        tickets = pickle.load(open('data/selTickets.pkl', 'rb'))
        MoneyTrace.fetchAllMinutePrice(tickets, tillDate=tillDate)
        return {'status':'ok', 'reason':'Intra data updated'}
    except Exception as e:
        print("Error: %s" % e)
        return {'status':'bad', 'reason':'Wrong param'}

if __name__ == '__main__':
    # scheduler = BackgroundScheduler() 
    # @scheduler.scheduled_job('cron', hour=17)
    # def endday_job():
    #     start_new_session()
    # scheduler.start()
    # atexit.register(lambda: scheduler.shutdown())
    # print("Scheduler is on, starting server...")

    # app.run(debug=True, host='localhost')
    socket_.run(app, debug=True)