from flask import Flask, render_template
from StrategySession import BacktestSession, Decision
from apscheduler.schedulers.background import BackgroundScheduler
import time, datetime, atexit, pickle

app = Flask(__name__)
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
    for s in db['sess'].signals:
        if s['dec'] != Decision.KEEP:
            res += "<p>[%s] %s : %s</p>" % (s['tic'], s['dec'], s['reason'])
    return res


if __name__ == '__main__':
    scheduler = BackgroundScheduler() 
    @scheduler.scheduled_job('cron', hour=17)
    def endday_job():
        start_new_session()
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    print("Scheduler is on, starting server...")

    app.run(debug=True, host='localhost')