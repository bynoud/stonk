
from http.client import NO_CONTENT
import StockAPI, Symbol
import pandas as pd
import numpy as np
import pickle, os
from datetime import datetime, timedelta
from pathlib import Path

_G = {
    'TODAY': None,
    'TRADEDAY': None,
    'REFETCH': 20, # refetch any missing data if it within 7 days
    'CACHED': {},
    'ABV_CACHED': {},
}

MAXDAY = 500

def updateTradingDays():
    today = datetime.now().strftime("%D")
    # print("Get today %s - %s - %s" % (today, _G['TODAY'], daynum), end='')
    # if _G['TODAY'] != today:
    _G['TRADEDAY'] = [datetime.fromtimestamp(x).replace(hour=15) for x in StockAPI.getTradingDate(MAXDAY)]
    _G['TODAY'] = today
    _G['ABV_CACHED'] = {}

def getTradingDayIndex(live):
    # _updateTradingDays()
    tdel = datetime.now() - _G['TRADEDAY'][-1]
    # print("TradingDays index", live, _G['TRADEDAY'][-1], tdel)
    if live or tdel.days >= 0:
        return 0
    return 1

def _getLastDate(daynum: int) -> datetime:
    # now = datetime.now()
    # today = now.strftime("%D")
    # # print("Get today %s - %s - %s" % (today, _G['TODAY'], daynum), end='')
    # if _G['TODAY'] != today:
    #     _G['TRADEDAY'] = [datetime.fromtimestamp(x).replace(hour=15) for x in StockAPI.getTradingDate(300)]
    #     _G['TODAY'] = today
    # # print(" -> %s" % (_G['TRADEDAY'][-1-daynum]))
    return _G['TRADEDAY'][-1-daynum]

# def _getPrice(ticket:str, fromDate: datetime, tillDate: datetime, resol:str):
#     return pd.DataFrame(StockAPI.getPriceHistory2(ticket,
#         fromDate=fromDate, tillDate=tillDate, resol=resol,  provider='mbs'))

# def migrate():
#     import os
#     # for inf in os.walk('data/intra1m_bk'):
#     # allf = list(os.walk('data/intra1m_bk'))
#     print('Start migrate...', end='')
#     for inf in os.walk('data/intra1m_bk'):
#         if len(inf[2]) == 0: continue

#         folder = inf[0]
#         ticket = os.path.basename(folder)
#         intras = {}

#         try:
#             os.mkdir('./data/intra1m/%s' % ticket[0].lower())
#         except:
#             pass

#         for fname in inf[2]:
#             date = fname[3:-4]
#             try:
#                 with open(folder + '/' + fname, 'rb') as fh:
#                     data = pickle.load(fh)
#                 intras[date] = data
#             except Exception as e:
#                 print("Error on open file: %s" % e)
#                 return
#         try:
#             with open('./data/intra1m/%s/%s-1m.pkl' % (ticket[0].lower(), ticket), 'wb') as fh:
#                 pickle.dump(intras, fh)
#         except Exception as e:
#             print("error when write new file: %s" % e)
#             return
        
#         print('.', end='')
#     print("Done")


def _getPriceMinute_old(ticket:str, dayNum:int=200, tillDate:int=0):
    print("Fetching Minute prices for '%s' last %0d days till %s ..." % (ticket, dayNum, _getLastDate(tillDate)))
    res = {'prices': [], 'lastNotFoundIdx': -1}
    # prices = pd.DataFrame()
    dataFolder = Path('./data/intra1m_bk/%s/%s' % (ticket[0].lower(), ticket))
    dataFolder.mkdir(parents=True, exist_ok=True)
    # lastNotFoundIdx = -1

    def appendResult(intra, date):
        #res['prices'] = pd.concat([res['prices'], intra], axis=0, ignore_index=True)
        # print("append %s - %s" % (date, intra.iloc[-1]))
        if intra is None or intra.empty:
            intra = pd.DataFrame({
                'high':[0], 'low':[0], 'open':[0],
                'close':[0], 'volumn':[0], 'time':date.timestamp()})
        intra['stamp'] = [datetime.fromtimestamp(x) for x in intra.time]
        res['prices'].append(intra)

    def dataFile(date):
        return (dataFolder / ('m1-%s.pkl' % date.strftime("%Y-%m-%d")))

    def fetchLastNotFound(endIdx):
        startIdx = res['lastNotFoundIdx']
        if startIdx < 0:
            return
        # print("fetch %s %0d - %0d" % (ticket, startIdx, endIdx))
        fromDate = _getLastDate(startIdx) - timedelta(1)
        intras = pd.DataFrame(StockAPI.getPriceHistory2(ticket,
                fromDate=fromDate.replace(hour=20),
                tillDate=_getLastDate(endIdx),
                resol="1",  provider='mbs'))
        
        for i in range(startIdx, endIdx-1, -1):
            thisDate = _getLastDate(i)
            dayIntra = intras[
                    (intras['time'] >= thisDate.replace(hour=1, minute=0).timestamp()) &
                    (intras['time'] <= thisDate.replace(hour=23, minute=0).timestamp())].reset_index(drop=True)
            appendResult(dayIntra, thisDate)
            if (datetime.now() - thisDate).days >= 0:
                # pickle.dump(dayIntra, open('%s/m1-%s.pkl' % (folderName, thisDate.strftime("%d-%m-%Y"), 'wb')))
                with dataFile(thisDate).open('wb') as fh:
                    # print("dumping %s %s -> %s" %(ticket, thisDate, dataFile(thisDate)))
                    # print(dayIntra.tail())
                    pickle.dump(dayIntra, fh)

        res['lastNotFoundIdx'] = -1

    for i in range(dayNum-1,tillDate-1,-1):
        today = _getLastDate(i)
        # print("geting Minute for '%s' in %s" % (ticket, today))
        try:
            with dataFile(today).open('rb') as fh: intra = pickle.load(fh)
            if intra.empty and i < _G['REFETCH']:
                raise Exception("Just to refetch")
            fetchLastNotFound(i+1)
            appendResult(intra, today)
        except:
            print("Not found %s" % (today))
            if res['lastNotFoundIdx'] < 0:
                res['lastNotFoundIdx'] = i
            if res['lastNotFoundIdx'] - i > 9 or i == tillDate:
                fetchLastNotFound(i)

    # for debug
    
    return res['prices']

def _getPriceMinute(ticket:str, dayNum:int=200, tillDate:int=0, getLive=False):
    # print("Fetching Minute prices for '%s' last %0d days till %s ..." % (ticket, dayNum, _getLastDate(tillDate)))
    res = {'prices': [], 'lastNotFoundIdx': -1, 'needWriteback': False}
    # prices = pd.DataFrame()
    # dataFolder = Path('./data/intra1m_bk/%s/%s' % (ticket[0].lower(), ticket))
    # dataFolder.mkdir(parents=True, exist_ok=True)
    # lastNotFoundIdx = -1

    foldern = './data/intra1m/%s/' % ticket[0].lower()
    filen = foldern + ticket + "-1m.pkl"
    if getLive:
        print("getlive data for %s" % ticket)
        _G['CACHED'][ticket] = {}

        try:
            os.remove(filen)
        except FileNotFoundError:
            pass
    else:
        try:
            _ = _G['CACHED'][ticket]
            # print("price from cache")
        except:
            try:
                with open(filen,'rb') as fh:
                    _G['CACHED'][ticket] = pickle.load(fh)
                    # print("price from file")
            except:
                _G['CACHED'][ticket] = {}
                # print("price empty")
    curprices = _G['CACHED'][ticket]

    def appendResult(intra, date):
        #res['prices'] = pd.concat([res['prices'], intra], axis=0, ignore_index=True)
        # print("append %s - %s" % (date, intra.iloc[-1]))
        if intra is None or intra.empty:
            intra = pd.DataFrame({
                'high':[0], 'low':[0], 'open':[0],
                'close':[0], 'volumn':[0], 'time':date.timestamp()})
        intra['stamp'] = [datetime.fromtimestamp(x) for x in intra.time]
        res['prices'].append(intra)

    # def dataFile(date):
    #     return (dataFolder / ('m1-%s.pkl' % date.strftime("%Y-%m-%d")))

    def fetchLastNotFound(endIdx):
        startIdx = res['lastNotFoundIdx']
        if startIdx < 0:
            return
        print("fetch %s %0d - %0d" % (ticket, startIdx, endIdx))
        fromDate = _getLastDate(startIdx) - timedelta(1)
        intras = pd.DataFrame(StockAPI.getPriceHistory2(ticket,
                fromDate=fromDate.replace(hour=20),
                tillDate=_getLastDate(endIdx),
                resol="1",  provider='mbs'))
        
        for i in range(startIdx, endIdx-1, -1):
            thisDate = _getLastDate(i)
            dayIntra = intras[
                    (intras['time'] >= thisDate.replace(hour=1, minute=0).timestamp()) &
                    (intras['time'] <= thisDate.replace(hour=23, minute=0).timestamp())].reset_index(drop=True)
            appendResult(dayIntra, thisDate)
            if (datetime.now() - thisDate).days >= 0:
                curprices[thisDate.strftime("%Y-%m-%d")] = dayIntra
                res['needWriteback'] = True
                # # pickle.dump(dayIntra, open('%s/m1-%s.pkl' % (folderName, thisDate.strftime("%d-%m-%Y"), 'wb')))
                # with dataFile(thisDate).open('wb') as fh:
                #     # print("dumping %s %s -> %s" %(ticket, thisDate, dataFile(thisDate)))
                #     # print(dayIntra.tail())
                #     pickle.dump(dayIntra, fh)

        with open(filen, 'wb') as fh: pickle.dump(curprices, fh)
        res['lastNotFoundIdx'] = -1

    for i in range(dayNum-1,tillDate-1,-1):
        today = _getLastDate(i)
        # print("geting Minute for '%s' in %s" % (ticket, today))
        try:
            intra = curprices[today.strftime("%Y-%m-%d")]
            if intra.empty and i < _G['REFETCH']:
                raise Exception("Just to refetch")
            fetchLastNotFound(i+1)
            appendResult(intra, today)
        except:
            # print("Not found %s" % (today))
            if res['lastNotFoundIdx'] < 0:
                res['lastNotFoundIdx'] = i
            if res['lastNotFoundIdx'] - i > 9 or i == tillDate:
                fetchLastNotFound(i)

    if res['needWriteback']:
        print("Writeback data for %s" % ticket)
        with open(filen, 'wb') as fh: pickle.dump(curprices, fh)

    # for debug
    
    return res['prices']

def ticketFilter(tickets=None, filerFunc='_default_'):
    if tickets is None:
        tickets = StockAPI.getAllTickets('hose hnx upcom')
    symbols = Symbol.getAllSymbolHistory(tickets=tickets)
    tradeDays = symbols['VNM'].time

    if filerFunc == '_default_':
        # filerFunc = lambda(x: x.len>=100 and x.sma(src='volumn',window=50).iloc[-1]>=100000)
        def _defaultFilter(x):
            return (
                x.len>50 and 
                x.time.iloc[-49] == tradeDays.iloc[-49] and # remove all ticket with non-trade days
                (x.sma(src='volumn',window=50).iloc[-1] * x.close.iloc[-1]) >= 7000000 and 
                2.0 < x.close.iloc[-1] < 110 and
                len(x.name) == 3 # To remove Derative ticket...
            )
        filerFunc = _defaultFilter
    symbols = {x.name:x for x in filter(filerFunc, symbols.values())}
    tickets = sorted(symbols.keys())
    pickle.dump(symbols, open('data/current_prices.pkl', 'wb'))
    pickle.dump(tickets, open('data/selTickets.pkl', 'wb'))

def fetchAllMinutePrice(tickets=None, dayNum=200, tillDate=0):
    updateTradingDays()
    tillDate = getTradingDayIndex(tillDate==0)
    if tickets is None:
        tickets = StockAPI.getAllTickets()
    for tic in tickets:
        _getPriceMinute(tic,dayNum,tillDate)

def updateAbvAll(tickets, tillDate):
    fetchAllMinutePrice(tickets, tillDate=tillDate)
    for tic in tickets:
        _G['ABV_CACHED'][tic] = _abvRsi(tic, tillDate=tillDate)

def AccumuleBalanceVolume(df, refPrice=None):
    if refPrice is None: refPrice = df.close.iloc[0]
    close1 = df.close.shift(1)
    close1.iloc[0] = refPrice
    diff = (df.close - close1) * 10 / close1
    hig = df.high.where(df.high > close1, close1)
    low = df.low.where(df.low < close1, close1)
    # Find the move direction
    direct = [1 if diff[0]>0 else (-1 if diff[0]<0 else 0)]
    for d in diff[1:]:
        direct.append(1 if d>0 else (-1 if d<0 else direct[-1]))
    df['movingDir'] = direct

    h2l = hig - low
    mfm_up = (df.close - low) / h2l
    mfm_dn = (hig - df.close) / h2l
    mfm = mfm_up.where(df.movingDir==1, mfm_dn).fillna(0) * diff + df.movingDir
    abv = mfm * df.volumn
    #debug
    df['abv'] = abv
    df['h'] = hig
    df['l'] = low
    df['mfm_up'] = mfm_up
    df['mfm_dn'] = mfm_dn
    df['mfm'] = mfm
    df['diff'] = diff

    return abv

def cci(df, win=20, const=0.015):
    tp = (df.high + df.low + df.close) / 3
    mad = lambda x: np.fabs(x - x.mean()).mean()
    sma = tp.rolling(window=win)
    return (tp - sma.mean()) / (const * sma.apply(mad, raw=True))

def _abvRsi(ticket,dayNum=200,tillDate=0, ignoreStartEnd=False, getLive=False):
    tillDate = getTradingDayIndex(tillDate==0)
    m1 = _getPriceMinute(ticket,dayNum,tillDate,getLive)
    daily = []
    refPrice = None
    for df in m1:
        if df.empty: continue
        abv = AccumuleBalanceVolume(df, refPrice)
        if ignoreStartEnd: abv = abv[1:-1]
        daily.append({'stamp':df.stamp[0],
                      'open':df.open.iloc[0], 'close':df.close.iloc[-1],
                      'high':df.high.max(), 'low':df.low.min(),
                      'volumn':df.volumn.sum(), 'time':df.time.iloc[0],
                      'buyVol':abv[abv>0].sum(), 'sellVol':-abv[abv<0].sum()})
        refPrice = df.close.iloc[-1]
        
    daily = pd.DataFrame(daily)
    daily['abvRsi'] = volRsi(daily.buyVol, daily.sellVol)
    daily['cci'] = cci(daily)
    # return [daily,m1]
    # print(daily.tail())
    return daily

def abvRsi(tic, tillDate=0, getLive=False, refresh=False):
    if refresh or getLive:
        updateTradingDays()
    if refresh or getLive or tic not in _G['ABV_CACHED']:
        _G['ABV_CACHED'][tic] = _abvRsi(tic, tillDate=tillDate, getLive=getLive)
    return _G['ABV_CACHED'][tic]

def getLowRsiTicket(tickets, tillDate):
    retTickets = []
    for tic in tickets:
        abv = abvRsi(tic, tillDate=tillDate)
        if abv['abvRsi'].iloc[-10:].min() < 0.5:
            retTickets.append(tic)
    return retTickets

def ema(ps, win):
    return ps.ewm(span=win, min_periods=win, adjust=False, ignore_na=False).mean()
def dema(ps, win):
    ema1 = ema(ps, win)
    ema2 = ema(ema1, win)
    return (2*ema1) - ema2

def volRsi(buyVol, sellVol, win=20):
    # chg = (buyVol - sellVol) / (buyVol + sellVol)
    # delta = chg
    delta = buyVol - sellVol # * 1.1 # give SellVol a 10% advantage?
    dUp, dDown = delta.copy(), delta.copy()
    dUp[dUp < 0] = 0
    dDown[dDown > 0] = 0
    # rolUp = dUp.rolling(window=win).mean()
    # rolDown = dDown.rolling(window=win).mean().abs()
    # rolUp = dUp.ewm(span=win, min_periods=win, adjust=False, ignore_na=False).mean()
    # rolDown = dDown.ewm(span=win, min_periods=win, adjust=False, ignore_na=False).mean().abs()
    rolUp = dema(dUp, win)
    rolDown = dema(dDown, win).abs()
    rs = (rolUp / rolDown).fillna(10000000000000)
    # print(rs.tail(10))
    return ( 100.0 - 100.0 / (1.0 + rs))

# def _consolidate(df):
#     df['pdiff'] = df['close'] - df['open']
#     df[]