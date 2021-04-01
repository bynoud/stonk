
import logging
from Symbol import SymbolHistory
from StrategyCommon import Decision, run_backtest
import Indicator
import pandas as pd

def double_ma_decision(maLong, maShort, idx: int = -1) -> (Decision, str):
    # It's simple, buy if shortMA break longMA, sell if shortMA corssdown
    if maShort.iloc[idx-1] <= maLong.iloc[idx-1] and maShort.iloc[idx] > maLong.iloc[idx]:
        return Decision.BUY, "Double MA Golden cross"
    if maShort.iloc[idx-1] >= maLong.iloc[idx-1] and maShort.iloc[idx] < maLong.iloc[idx]:
        return Decision.SELL, "Double MA Death cross"
    return Decision.KEEP, "Double MA no cross"

def triple_ma_decision(maLong, maMedium, maShort, idx: int = -1) -> (Decision, str):
    if (maShort.iloc[idx-1] <= maMedium.iloc[idx-1] or maShort.iloc[idx-1] <= maLong.iloc[idx-1]) and \
        (maShort.iloc[idx] > maMedium.iloc[idx] and maShort.iloc[idx] > maLong.iloc[idx]):
        return Decision.BUY, "Triple MA Golden cross"
    if (maShort.iloc[idx-1] >= maMedium.iloc[idx-1] and maShort.iloc[idx-1] >= maLong.iloc[idx-1]) and \
        (maShort.iloc[idx] < maMedium.iloc[idx]):
        return Decision.BUY, "Triple MA Death cross"
    return Decision.KEEP, "Triple MA No cross"

def ma_psar_decision(psarTrend, maLong, maShort, idx: int = -1) -> (Decision, str):
    if not psarTrend.iloc[idx-1] and psarTrend.iloc[idx] and maShort.iloc[idx] > maLong.iloc[idx]:
        return Decision.BUY, 'PSAR switch to bullish with Double MA positive'
    if (psarTrend.iloc[idx-1] and not psarTrend.iloc[idx]) and maShort.iloc[idx] <= maLong.iloc[idx]:
        return Decision.SELL, 'PSAR switch to bearish when Double MA is negative'
    if (maShort.iloc[idx-1] >= maLong.iloc[idx-1] and maShort.iloc[idx] < maLong.iloc[idx]) and \
        not psarTrend.iloc[idx]:
        return Decision.SELL, 'Double MA Death cross when PSAR is bearish'
    return Decision.KEEP, "PSAR & Double MA don't give any sign"

def double_ma_list(shortWinLimit=[5,14], maxWin=80):
    res = []
    for sw in range(shortWinLimit[0],shortWinLimit[1]+1):
        for lw in range(min(int(sw*1.5), maxWin), min(int(sw*3), maxWin)+1):
            if [lw,sw] not in res:
                res.append([lw,sw])
    return res

def triple_ma_list(shortWinLimit=[5,14], maxWin=80):
    res = []
    for sw in range(shortWinLimit[0],shortWinLimit[1]+1):
        for mw in range(min(int(sw*1.5), maxWin), min(int(sw*2.5), maxWin)+1):
            for lw in range(min(int(mw*1.5), maxWin), min(int(mw*2.5), maxWin)+1):
                if [lw,mw,sw] not in res:
                    res.append([lw,mw,sw])
    return res

def double_ma_retrace(maLong, maShort, price):
    maDiff = maShort - maLong
    priceDiff = {}
    _diff = {}
    priceDiff[3] = price.diff(3).shift(-3) # On T3, check for different with T0 price
    priceDiff[4] = price.diff().shift(-4) # diff between T3 & T4
    priceDiff[5] = price.diff().shift(-5)
    _diff[3] = priceDiff[3] # If stop at T3, mean T3 is negative, save this negative as result
    _diff[4] = _diff[3] # if stop as T4, save T3 diff as result
    _diff[5] = price.diff(4).shift(-4) # if stop as T5, save T4 as result
    _diff[6] = price.diff(5).shift(-5) # if stop as T6, save T5 as result
    res = {'gold':[], 'death':[]}
    for idx in range(30, len(price)-5):
        if maDiff[idx-1] <= 0 and maDiff[idx] > 0:
            # look ahead to confirm the price
            for p in range(3,6):
                if priceDiff[p][idx] < 0:
                    res['gold'].append([idx, p-1, _diff[p][idx]])
                    break
            else:
                # No break, so no negative is found
                res['gold'].append([idx, 5, _diff[6][idx]])
        if maDiff[idx-1] >= 0 and maDiff[idx] < 0:
            for p in range(3,6):
                if priceDiff[p][idx] > 0:
                    res['death'].append([idx, p-1, _diff[p][idx]])
                    break
            else:
                # No break, so no negative is found
                res['death'].append([idx, 5, _diff[6][idx]])
    if len(res['gold']) == 0: res['gold'].append([0,0,0])
    if len(res['death']) == 0: res['death'].append([0,0,0])
    return {'gold': pd.DataFrame( 
                 {'diff': [x[2]*3 if x[1]<3 else x[2] for x in res['gold']], # punish for failed signal more by *3
                  't': [x[1] for x in res['gold']],
                  'idx': [x[0] for x in res['gold']]}),
          'death': pd.DataFrame( 
                 {'diff': [x[2]*3 if x[1]<3 else x[2] for x in res['death']],
                  't': [x[1] for x in res['death']],
                  'idx': [x[0] for x in res['death']]} )}
    
def get_best_ma_psar(symbol: SymbolHistory, shortWinLimit=[5,14], maxWin=80):
    testListDouble = []
    testListTriple = []
    result = {'double':[], 'triple':[]}
    for sw in range(shortWinLimit[0],shortWinLimit[1]+1):
        for lw in range(min(int(sw*1.5), maxWin), min(int(sw*2.5), maxWin)+1):
            if [lw,sw] not in testListDouble:
                testListDouble.append([lw,sw])
    for sw in range(shortWinLimit[0],shortWinLimit[1]+1):
        for mw in range(min(int(sw*1.5), maxWin), min(int(sw*2.5), maxWin)+1):
            for lw in range(min(int(mw*1.5), maxWin), min(int(mw*2.5), maxWin)+1):
                if [lw,mw,sw] not in testListTriple:
                    testListTriple.append([lw,mw,sw])

    print('Finding best Double MA matched for "%s" with %d combination . . .' %
         (symbol.name, len(testListDouble)), end='', flush=True)
    cnt = 100
    for lw,sw in testListDouble:
        res = run_backtest(symbol, ma_psar_decision, {'long':lw, 'short':sw})
        # for now only check for winrate
        # if res.winPerc > 0.6: result['double'].append({'win':[lw,sw], 'res':res})
        result['double'].append({'win':[lw,sw], 'res':res})
        cnt -= 1
        if cnt <= 0:
            print(' .', end='', flush=True)
            cnt = 100
    print(" Done")

    # print('Finding best Triple MA matched for "%s" with %d combination . . .' % 
    #     (symbol.name, len(testListTriple)), end='', flush=True)
    # cnt = 100
    # for lw,mw,sw in testListTriple:
    #     res = run_backtest(symbol, triple_ma_decision, {'long':lw, 'medium':mw, 'short':sw})
    #     # for now only check for winrate
    #     # if res.winPerc > 0.6: result['triple'].append({'win':[lw,mw,sw], 'res':res})
    #     result['triple'].append({'win':[lw,mw,sw], 'res':res})
    #     cnt -= 1
    #     if cnt <= 0:
    #         print(' .', end='', flush=True)
    #         cnt = 100
    # print(" Done")

    return result

def get_best_double_ma(symbol: SymbolHistory, func=None, filter=True):
    print("Finding the best match for Double MA of '%s' ..." % symbol.name, end='', flush=True)
    res = []
    cnt = 20
    price = Indicator.exponential_moving_average(symbol.close,6).shift(-3) # this is better to indicate the trend on some next day
    if func is None: func = symbol.sma
    for lw,sw in double_ma_list():
        maShort = func(sw)
        maLong = func(lw)
        trace = double_ma_retrace(maLong, maShort, price)
        res.append({'win':[lw,sw], 
                'gold': [trace['gold']['diff'].mean().round(2), trace['gold']['diff'].std().round(2),
                     trace['gold']['t'].mean().round(2), trace['gold']['t'].std().round(2)],
            'death': [trace['death']['diff'].mean().round(2), trace['death']['diff'].std().round(2),
                     trace['death']['t'].mean().round(2), trace['death']['t'].std().round(2)],})
        cnt -= 1
        if cnt == 0:
            print('.', end='', flush=True)
    print(" Done")
    
    if filter:
        best = res[0]
        for r in res:
            if r['gold'][0] >= best['gold'][0] and r['gold'][2] >= 3:
                ok = True
                if r['gold'][0] == best['gold'][0]:
                    if r['gold'][1] < best['gold'][1]:
                        ok = False # std of Gold is smaller, dont take it
                    elif r['death'][0] > best['death'][0]:
                        ok = False # negative is smaller
                if ok:
                    best = r
        return best
    else:
        return res


def check_best_match_triple_sma(symbol: SymbolHistory, shortWinLimit=[5,14], maxWin=80):
    testListTriple = []
    result = []
    for sw in range(shortWinLimit[0],shortWinLimit[1]+1):
        for mw in range(min(int(sw*1.5), maxWin), min(int(sw*3), maxWin)+1):
            for lw in range(min(int(mw*1.5), maxWin), min(int(mw*3), maxWin)+1):
                if [lw,mw,sw] not in testListTriple:
                    testListTriple.append([lw,mw,sw])
    print('Finding best Triple MA matched for "%s" with %d combination . . .' % 
        (symbol.name, len(testListTriple)), end='', flush=True)
    cnt = 100
    for lw,mw,sw in testListTriple:
        res = run_backtest(symbol, triple_ma_decision, {'longWin':lw, 'mediumWin':mw, 'shortWin':sw})
        result.append({'win':[lw,mw,sw], 'res':res})
        cnt -= 1
        if cnt <= 0:
            print(' .', end='', flush=True)
            cnt = 100
    print(" Done")

    return result