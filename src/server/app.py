from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from apscheduler.schedulers.background import BackgroundScheduler
import time, datetime, atexit, pickle
import pandas as pd

from StrategySession import BacktestSession, Decision
from Symbol import SymbolHistory
import StockAPI, Statistics

app = Flask(__name__)
CORS(app)

db = {'sess': None}

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
    return render_template('index.html')

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
        sym = pickle.load(open('data/tmp_price_%s.pkl' % ticket, 'rb'))
    except:
        # sym = SymbolHistory(ticket, StockAPI.getPriceHistory(ticket, 365*2+50))
        sym = StockAPI.getPriceHistory(ticket, 365)
        pickle.dump(sym, open('data/tmp_price_%s.pkl' % ticket, 'wb'))
    df = pd.DataFrame(sym)
    return {'status':'ok', 'payload': df.to_dict(orient='records')}

if __name__ == '__main__':
    scheduler = BackgroundScheduler() 
    @scheduler.scheduled_job('cron', hour=17)
    def endday_job():
        start_new_session()
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    print("Scheduler is on, starting server...")

    app.run(debug=True, host='localhost')