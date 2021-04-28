
import pandas as pd
import numpy as np

import StockAPI
from datetime import datetime

def intraMatchedVol(ticket, dates=None, noOpenClose=True):
    if dates is None:
        dates = StockAPI.getTradingDate(2)
    intras = StockAPI.getIntradayHistory(ticket, dates=dates, matchedOnly=True)
    for i in range(len(intras)):
        df = intras[i]

        if df is None:
            intras[i] = pd.DataFrame({'mp':[0], 'mv':[0], 'buy':[-1], 'date':pd.Timestamp(dates[i], unit='s')})
            continue

        if noOpenClose:
            df = df[1:-1]
        # reduce number of matched
        diff = np.where((df['mp'] != df['mp'].shift(1)) | (df['buy'] != df['buy'].shift(1)), 1, 0)
        df = df.groupby(diff.cumsum()).agg({'mp':'first', 'mv': 'sum', 'buy':'first'})
        # df = df.reset_index(drop=True)
        df['date'] = pd.Series(pd.Timestamp(dates[i], unit='s'), index=df.index)

        intras[i] = df

    df = pd.concat(intras, ignore_index=True)
    # df['date1'] = df['date'].shift(1)
    # df['fmt'] = np.where(df['date'].dt.year != df['date1'].dt.year, '%Y', '')
    # df.at[df['fmt']=='' & (df['date'].dt.month != df['date1'].dt.month), 'fmt'] = '%b'
    # df.at[df['fmt']=='' & (df['date'].dt.day != df['date1'].dt.day), 'fmt'] = '%d'

    df['label'] = pd.Series('', index=df.index)

    lastDay = df.at[0, 'date']
    df.at[0, 'label'] = lastDay.strftime('%d')
    for i in range(len(df)):
        today = df.at[i, 'date']
        fmt = '%Y' if today.year != lastDay.year else \
            '%b' if today.month != lastDay.month else \
                '%d' if today.day != lastDay.day else ''
        label = today.strftime(fmt)
        if fmt != '':
            # print(i, fmt,label)
            df.at[i,'label'] = label
        lastDay = today

    # Using log, to scale down the outlier volumn
    # df['vol'] = np.log2(df['mv'])
    df['vol'] = df['mv'].copy()

    df['buyVol'] = np.where(df['buy']==1, df['vol'], 0)
    df['sellVol'] = np.where(df['buy']==0, df['vol'], 0)
    df['unkVol'] = np.where(df['buy']==-1, df['vol'], 0)
    df['buyPerc'] = (df['buyVol'].rolling(window=40).mean().fillna(0) * 100.0 /
        df['vol'].rolling(window=40).mean().fillna(1)).round(1)
    # df['volSum'] = df['vol'].cumsum()
    return df[['label','mp','mv','vol','buyVol','sellVol','unkVol','buyPerc','buy']]

def intraMatchedVol2(ticket, dates=None, noOpenClose=True):
    df = intraMatchedVol(ticket, dates, noOpenClose)
    res = []
    idx = 0
    for i in range(len(df)):
        d = df.iloc[i]
        vol = int(d['vol'])
        first = True
        while vol > 0:
            if vol > 40000:
                deep, cnt = 5, 20000
            elif vol > 20000:
                deep, cnt = 4, 10000
            elif vol > 10000:
                deep, cnt = 3, 5000
            elif vol > 5000:
                deep, cnt = 2, 2000
            elif vol > 2000:
                deep, cnt = 1, 1000
            elif vol > 1000:
                deep, cnt = 0, 1000
            else:
                deep, cnt = 0, vol

            res.append({
                'idx': idx,
                'vol': cnt, 'weight': deep,
                'label': d['label'] if first else '',
                'buy': int(d['buy']), 'price': d['mp']
                })
            first = False
            vol -= cnt
            idx += 1
    print(len(res))
    return res

def intraSum(intra):
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


    return res

def volRsi(buyVol, sellVol):
    # chg = (buyVol - sellVol) / (buyVol + sellVol)
    # delta = chg
    delta = buyVol - sellVol # * 1.1 # give SellVol a 10% advantage?
    dUp, dDown = delta.copy(), delta.copy()
    dUp[dUp < 0] = 0
    dDown[dDown > 0] = 0
    rolUp = dUp.rolling(window=14, min_periods=1).mean()
    rolDown = dDown.rolling(window=14, min_periods=1).mean().abs()
    rs = rolUp / rolDown
    # print(rs.tail(10))
    return ( 100.0 - 100.0 / (1.0 + rs))

def dailyStat(symbol, lookback=100, intras=None):
    period = lookback + 14
    dates = symbol.time.iloc[-period:].reset_index(drop=True)
    if intras is None:
        intras = StockAPI.getIntradayHistory(symbol.name, dates=dates, matchedOnly=True)

    close = symbol.close.iloc[-period:].reset_index(drop=True)
    df = pd.DataFrame({
        'close': close,
        'vol': symbol.volumn.iloc[-period:].reset_index(drop=True),
        'dates': pd.to_datetime(dates, unit='s'),
        # 'chg': close.diff() / close.shift(1),
        'volAvg': symbol.volumn.rolling(window=50, min_periods=50).mean().shift(1).iloc[-period:].reset_index(drop=True),
        'buyVol': pd.Series(0.0, index=range(period)),
        'sellVol': pd.Series(0.0, index=range(period)),
        'buyPrice': pd.Series(0.0, index=range(period)),
        'sellPrice': pd.Series(0.0, index=range(period)),
    })

    for i in range(period-1, -1, -1):
        date = dates[i]
        intr = intras[i]

        if intr is not None:
            buy = intr[intr['buy']==1]
            sell = intr[intr['buy']!=1]
            buyVol, sellVol = buy['mv'].sum(), sell['mv'].sum()
            buyPrice = 0 if buyVol == 0 else (buy['mv'] * buy['mp']).sum() / buy['mv'].sum()
            sellPrice = 0 if sellVol == 0 else (sell['mv'] * sell['mp']).sum() / sell['mv'].sum()
            df.at[i, 'buyVol'] = buyVol
            df.at[i, 'buyPrice'] = buyPrice
            df.at[i, 'sellVol'] = sellVol
            df.at[i, 'sellPrice'] = sellPrice
            
    df['buySellVolRatio'] = df['buyVol'] / df['sellVol']
    df['buySellPriceDiff'] = df['buyPrice'] - df['sellPrice']
    df['rsi'] = symbol.rsi().iloc[-period:].reset_index(drop=True)
    df['rsiChg'] = df['rsi'].diff() # * 100.0 / df['rsi'].shift(1)
    df['volRsi'] = volRsi(df['buyVol'], df['sellVol'])
    df['volRsiChg'] = df['volRsi'].diff() # * 100.0 / df['volRsi'].shift(1)
    return df
