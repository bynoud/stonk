
import numpy as np
import pandas as pd
import StockAPI
from Symbol import SymbolHistory
import Statistics

# Some of the point you may want to enter:
#   + Big MoneyIn, or a BuyPower when price drop after trend had been breakout, average BuyPower >= 30
#   + BuyPower & MoneyIn happend witn 5 days, and Average BuyPower is >= 50%
#   + 3 consecutive BuyPower, Average BuyPower >= 30%
def checkMoneyFlowOld(symbol: SymbolHistory, lookback=20, intras=None, halfsess=False):
    period = lookback + 10
    dates = symbol.time.iloc[-period:].reset_index(drop=True)
    if intras is None:
        intras = StockAPI.getIntradayHistory(symbol.name, dates=dates)

    close = symbol.close.iloc[-period:].reset_index(drop=True)
    df = pd.DataFrame({
        'close': close,
        'chg': close.diff() / close.shift(1),
        'volAvg': symbol.volumn.rolling(window=50, min_periods=50).mean().shift(1).iloc[-period:].reset_index(drop=True),
        'buyVol': pd.Series(1, index=range(period)),
        'sellVol': pd.Series(1, index=range(period)),
        'bidVol': pd.Series(1, index=range(period)),
        'askVol': pd.Series(1, index=range(period)),
    })

    if halfsess:
        df['volAvg'].iloc[-1] = df['volAvg'].iloc[-1] * 2 / 3 # reduce the last Average

    for i in range(period):
        intr = intras[i]
        if intr is not None:
            unk = intr[intr['buy']==-1]
            if (float(len(unk)) / len(intr)) > 0.3:
                continue # The intra is too inconsistent, better to ignore it
            power = checkIntraSidePower(intr)
            df['buyVol'].at[i] = power['buy'].sum()
            df['sellVol'].at[i] = power['sell'].sum()
            df['bidVol'].at[i] = power['bid'].sum()
            df['askVol'].at[i] = power['ask'].sum()

    df['volPerc'] = (df['buyVol'] + df['sellVol']) / df['volAvg']
    df['volDiff'] = (df['buyVol'] - df['sellVol']) / (df['buyVol'] + df['sellVol'])
    df['volDiffAvg'] = df['volDiff'].rolling(window=10, min_periods=10).mean()
    df['BuyBid'] = df['buyVol'] / df['bidVol']
    df['SellAsk'] = df['sellVol'] / df['askVol']
    df['BidPower'] = df['BuyBid'] / df['SellAsk']

    signal = []
    for i in range(10, period):
        p = df.loc[i]
        s = ''
        if p['volDiff'] >= 0.9:
            s += 'DiffVol>=90 '
        if p['volDiffAvg'] >= 0.5:
            s += 'BuyPowerAvg>50% '
        if p['chg'] < 0 and p['volDiff'] > 0.6:
            s += 'PriceDropButHasBuyPower '
        if p['volDiff'] > 0.8 and p['volPerc'] > 1.5:
            s += 'BigMoneyIn '
        if p['BidPower'] >= 15 and p['BuyBid'] >= 2 and p['SellAsk'] < 0.6 and p['volPerc'] >= 1:
            s += 'FAKESELL '
        signal.append(s)
    
    return signal, df

def checkMoneyFlow(symbol: SymbolHistory, lookback=20, intras=None, halfsess=False):
    period = lookback+14
    # dates = symbol.time.iloc[-period:].reset_index(drop=True)

    priceChg = symbol.close.diff().iloc[-period:].reset_index(drop=True)
    dailyStat = Statistics.dailyStat(symbol, lookback=lookback)

    signal = []
    for i in range(14, period):
        p = dailyStat.loc[i]
        s = ''
        if priceChg[i] < 0 and p['volRsiChg'] >= 20:
            s += 'VolRsiBigIncWhenPriceDrop '
        if priceChg[i] < 0 and p['volRsiChg'] > 8 and p['volRsi'] > 60:
            s += 'VolRsiRecoverWhenPriceDrop '
        if p['volRsiChg'] >= 15 and p['volRsi'] > 50:
            s += 'VolRsiBigInc>50 ' 
        if all([p['volRsiChg'] > 0, dailyStat.loc[i-1]['volRsiChg'] > 0,
                priceChg[i] < 0, priceChg[i-1] < 0]):
            s += 'VolRsiPosDiver '
        if p['volRsiChg'] - dailyStat.loc[i-1]['volRsiChg'] >= 20:
            s += 'VolRsiBigSwing '
        # if p['volRsi'] > 85:
        #     s += 'VolRsi>85'
        signal.append(s)
    
    return signal, dailyStat

def checkMoneyFlowAll(symbols, lookback=20, halfsess=False):
    res = {}
    for tic,sym in symbols.items():
        try:
            res[tic] = checkMoneyFlow(sym, lookback, halfsess=halfsess)
        except Exception as e:
            print("Error to check Intra for '%s': %s" % (tic, e))
            res[tic] = None
    return res

def printMF(symbol, money):
    import datetime
    dates = symbol.time.iloc[-len(money[0]):].reset_index(drop=True)
    for s in range(len(money[0])):
        i = money[1].loc[s+10]
        print(" %s - %0.2f - %0.2f - %0.2f - %s" % (datetime.datetime.fromtimestamp(dates[s]), i['volPerc'], i['volDiff'], i['volDiffAvg'], money[0][s]))

def checkIntraSidePower(intra):
    df = intra.copy()
    df['_dt'] = pd.to_datetime(df['time'])
    df = df[(df['_dt'].dt.hour < 14) | (df['_dt'].dt.minute < 30)].reset_index(drop=True) # remove ATC phase
    df['_m'] = df['mt'].diff()
    offerVol = {}
    bidVol = {}
    buyVol = {}
    sellVol = {}
    prices = set()

    def _addPriceMax(l, p, v):
        if p == 0: return
        if p not in l: l[p] = 0
        if l[p] < v: l[p] = v
        prices.add(p)

    for i in range(len(df)):
        cur = df.loc[i]
        for i in range(1,4):
            _addPriceMax(offerVol, cur['op%d'%i], cur['ov%d'%i])
            _addPriceMax(bidVol, cur['bp%d'%i], cur['bv%d'%i])

        if cur['_m'] > 0:
            _t = buyVol if cur['buy']==1 else sellVol
            try:
                _t[cur['mp']] += cur['mv']
            except:
                _t[cur['mp']] = cur['mv']

    prices = sorted(prices)
    res = pd.DataFrame({
        'price': prices,
        'bid': [bidVol[x] if x in bidVol else 0 for x in prices],
        'buy': [buyVol[x] if x in buyVol else 0 for x in prices],
        'sell': [sellVol[x] if x in sellVol else 0 for x in prices],
        'ask': [offerVol[x] if x in offerVol else 0 for x in prices],
    })

    # report
    # for p in sorted(prices):
    #     print("%0.2f : bid %-06d buy %-06d sell %-06d ask %-06d" % (p,
    #         bidVol[p] if p in bidVol else 0,
    #         buyVol[p] if p in buyVol else 0,
    #         sellVol[p] if p in sellVol else 0,
    #         offerVol[p] if p in offerVol else 0,
    #     ))
    # print("Average: bid %0.2f buy %0.2f sell %0.2f ask %0.2f" % (
    #     (res['bid'] * res['price']).sum() / res['bid'].sum(),
    #     (res['buy'] * res['price']).sum() / res['buy'].sum(),
    #     (res['sell'] * res['price']).sum() / res['sell'].sum(),
    #     (res['ask'] * res['price']).sum() / res['ask'].sum()
    # ))
    # print("TotalVol: bid %-06d buy %-06d sell %-06d ask %-06d" % (
    #     res['bid'].sum(), res['buy'].sum(), res['sell'].sum(), res['ask'].sum()
    # ))

    return res

