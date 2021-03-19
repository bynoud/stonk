
from enum import Enum
import pandas as pd
import json
import datetime
import Indicator as si
import StockAPI

Decision = Enum('Decision', 'BUY SELL KEEP NONE')

_G = {'DEBFILE': None,
    'DEBUG': False
}

# It's a medium term investment, backtest show good result on VNM
# May take some time to close (backtest on VNM could take 3/4 months of holding position)
#   RSI downtrend < 30% & MACDHist < 0 -> Buy next day ATO
#   Sell when:
# 	+ MACD > 0 & RSI > 70
# 	+ MACDHist from positive to negative in last 2 days & RSI down also
# 		-> most risk
#     + MACDHist from positive to negative in last 2 days
# 		-> more risk
# 	+ MACDHist reduced in last day -> less risk, less reward
	 
# 	+ If RSI jump above 30 then down under 30 again -> get out (and MACDHist < 0)
# 	+ If RSI is not recover > 30 more than 4 day -> sell at day 5
def simple_MACD_RSI_decision(macdHist: pd.Series, rsi: pd.Series, inPos: int, atInd: int = -1):
    if atInd < 0: atInd = len(rsi)
    hi = atInd + 1
    li = atInd - 4

    rsiLast = list(rsi.iloc[li:hi])
    histLast = list(macdHist.iloc[li:hi])
    rsiDiffLast = list(rsi.iloc[li:hi].diff())
    histDiffLast = list(macdHist.iloc[li:hi].diff())

    # _G['DEBFILE'].write("--- ckecing %0d %0d - %s %s- %s %s \n" % (atInd, inPos, rsiLast, rsiDiffLast, histLast, histDiffLast))

    if not inPos:
        if rsiLast[-1] < 30 and histLast[-1] < 0:
            return (Decision.BUY, "Just buy it")
    
    else:
        # Go out if RSI cannot recover in last 4 days
        if all(i < 30 for i in rsiLast):
            return (Decision.SELL, "RSI cannot recover in 4 days")
        # Out if RSI over 30, but slump again
        if rsiLast[-2] >= 30 and rsiLast[-1] < 30:
            return (Decision.SELL, "RSI break down after recovered")
        # Close conditions
        if histLast[-1] > 0 and rsiLast[-1] >= 70:
            return (Decision.SELL, "Take profit at peak")
        if histLast[-3] >= 0 and histLast[-2] < 0 and histLast[-1] < 0:
            #return SELL #  out when MACD cross to negative in 2 conscutive days
            if rsiDiffLast[-1] < 0 and rsiDiffLast[-2] < 0:
                return (Decision.SELL, "Both RSI & MACD down in 2 consecutive days") # also check for RSI to dip # higher risk
        # less risk, by SELL at peak of MACD
        #if histDiffLast[-1] < 0:
        #    return SELL
        return (Decision.KEEP, "No sign of close")
    
    return (Decision.KEEP, "ERROR: Should not be there")

def psIloc(ps: pd.Series, atInd: int, size: int):
    if atInd < 0: atInd = len(ps) + 1 + atInd
    return ps.iloc[atInd-size:atInd]

# window must be  >= 4
# 1 is up, -1 is down, 0 is unsure
def rollingDirection(ps: pd.Series, window: int, atInd: int):
    sel = psIloc(ps, atInd, window)
    maDiff = list(sel.rolling(window=2).mean().diff())
    if maDiff[-1] < 0 and maDiff[-2] <= 0:
        return -1
    elif maDiff[-1] > 0 and maDiff[-2] >= 0:
        return 1
    else:
        return 0


def simple_moving_average_decision(longMA: pd.Series, mediumMA: pd.Series, shortMA: pd.Series, atInd: int = -1):
    longRoll = rollingDirection(longMA, 4, atInd)
    mediumRoll = rollingDirection(mediumMA, 4, atInd)
    shortRoll = rollingDirection(shortMA, 4, atInd)

    if longRoll >= 0 and mediumRoll > 0 and shortRoll > 0:
        if (longMA.iloc[-1] < mediumMA.iloc[-1] < shortMA.iloc[-1]) and \
            ( (longMA.iloc[-2] >= mediumMA.iloc[-2]) or 
              (mediumMA.iloc[-2] >= shortMA.iloc[-2]) or
              (longMA.iloc[-2] >= shortMA.iloc[-2])):
            return Decision.BUY, "Long MA < Medium MA < short MA"
        else:
            return Decision.KEEP, "Seem to still goging up"
    # maybe need other idicators here...     
    if shortRoll < 0 and mediumRoll < 0 and shortMA.iloc[-1] < mediumMA.iloc[-1]:
        return Decision.SELL, "Short MA is cross-down Medium MA"
    if shortRoll < 0 and rollingDirection(shortMA, 4, atInd-1):
        return Decision.SELL, "Short MA is dipping 2 continous days"
    
    return Decision.KEEP, "No sign is found"

STRATEGIES = {
    'SimpleMacdRsi': simple_MACD_RSI_decision,
}

def run_strategy(ps: pd.Series, strategyDecision, stopLossChk = None):
    macdHist = si.ma_convergence_divergence(ps)['hist']
    rsi = si.relative_strength_index(ps)

    ema50 = si.exponential_moving_average(ps, 50)
    ema21 = si.exponential_moving_average(ps, 21)
    ema14 = si.exponential_moving_average(ps, 14)

    lastBuyIdx = -1

    for idx in range(50, len(ps)):
        if idx - lastBuyIdx < 2: continue   # Not T2 yet, we only can sell at T3

        dec, reason = Decision.NONE, ""

        if lastBuyIdx >= 0:
            # Stop loss
            if stopLossChk != None and stopLossChk(ps[idx], idx):
                dec, reason = Decision.SELL, "Stop Loss"
            # elif idx - lastBuyIdx < 4:
            #     dec, reason = Decision.KEEP, "Should keep it at least 4 days"

        if dec == Decision.NONE:
            # FIXME: make some way to seletively run function# dec, reason = strategyDecision(macdHist, rsi, False if lastBuyIdx<0 else True, idx)
            dec, reason = simple_moving_average_decision(ema50, ema21, ema14, idx)

        if dec == Decision.BUY:
            if lastBuyIdx < 0:
                lastBuyIdx = idx+1
            else: # Already in possition
                dec = Decision.KEEP
        elif dec == Decision.SELL:
            if lastBuyIdx > 0:
                lastBuyIdx = -1
            else:
                dec = Decision.KEEP

        yield (dec, reason, idx)


def run_backtest(strategyName: str, price: {'open':pd.Series, 'close':pd.Series}, stopLoss: float = -10, maxHoldDay:int=40, shares: int = 1000):
    buyPrice = -1
    buyIdx = -1
    # _G['DEBFILE'] = open('debug.log', 'w')

    maxCap = -1
    profit = 0
    profitPerc = 0
    winCnt = 0
    tradeCnt = 0
    maxDay = -1

    buyNow = False
    sellNow = False

    def stopLossChk(closePrice, curIdx):
        # Stop loss
        loss = closePrice - buyPrice
        loss = float(loss) * 100.0 / buyPrice
        if loss < stopLoss:
            return True
        # Too long, just go out
        if curIdx - buyIdx > maxHoldDay:    # 2 months
            return True
        return False

    maxIdx = len(price['close'])-1
    for dec, reason, idx in run_strategy(price['close'], STRATEGIES[strategyName], stopLossChk):
        if dec == Decision.BUY:
            if idx == maxIdx:
                buyNow = True
                if _G['DEBUG']: print(" ----> BUY NOW")
            else:
                buyIdx = idx+1
                buyPrice = price['open'][buyIdx]
                cap = buyPrice * shares
                if cap > maxCap: maxCap = cap
                if _G['DEBUG']: print(" idx %0d : BUY  @ %0.3f '%s'" % (idx, buyPrice, reason))
        elif dec == Decision.SELL:
            if idx == maxIdx:
                sellNow = True
                if _G['DEBUG']: print(" ----> SELL NOW")
            else:
                sellPrice = price['open'][idx+1]
                diffPrice = sellPrice - buyPrice
                diffPerc = float(diffPrice) / buyPrice
                profit += diffPrice * shares
                profitPerc += diffPerc
                tradeCnt += 1
                if diffPrice > 0: winCnt += 1
                posDays = idx+1 - buyIdx
                if posDays > maxDay: maxDay = posDays
            if _G['DEBUG']: print(" idx %0d : SELL @ %0.3f profit %0.2f (%0.2f%%) '%s'" % (idx, sellPrice, diffPrice, diffPerc*100, reason))
        
    # print("Total Trade: %0d (maxCap %0.2f) Win %0d (%0.2f) profit %0.2f (%0.2f%%)" % (
    #     tradeCnt, maxCap, winCnt, float(winCnt)*100/tradeCnt, profit, profitPerc*100
    # ))
    # _G['DEBFILE'].close()
    return {'actionNow': "SELL" if sellNow else "BUY" if buyNow else "NONE",
            'tradeCnt':tradeCnt, 'winCnt': winCnt, 
            'winPerc': 0 if tradeCnt==0 else (float(winCnt)/tradeCnt),
            'maxCap': maxCap, 'maxDay': maxDay,
            'profit': profit, 'profitPerc': profitPerc}

# def simple_MACD_RSI_backtest_all(stopLoss: float = -10, maxHoldDay:int=40, shares: int = 1000):
#     numDay = 365*2 + 50
#     tickets = StockAPI.getAllSymbols('hose')
#     res = {}
#     for tic in tickets:
#         print(" Back testing '%s'" % tic)
#         price = pd.DataFrame(StockAPI.getPriceHistory(tic, numDay))
#         if len(price['close'] > 100):
#             res[tic] = simple_MACD_RSI_backtest(price, stopLoss, maxHoldDay, shares)
#     return res

# def simple_MACD_RSI_backtest_all(priceHist, stopLoss: float = -10, maxHoldDay:int=40, shares: int = 1000):
#     res = {}
#     for tic, price in priceHist.items():
#         print(" Back testing '%s'" % tic)
#         if len(price['close']) > 100:
#             res[tic] = simple_MACD_RSI_backtest(price, stopLoss, maxHoldDay, shares)
    
#     # report
#     for k,v in res.items():
#         if v['winPerc'] > 0.6 and v['tradeCnt'] >= 4:
#             print("  %s - trade %0d win %0d (%0.2f%%) profit %0.2f (%0.2f%%) maxCap %0.2f maxHold %0d" % 
#                 (k, v['tradeCnt'], v['winCnt'], v['winPerc']*100, v['profit'], v['profitPerc']*100, v['maxCap'], v['maxDay']))
#             if v['buyNow']: print("        -----> BUY NOW")
#     return res

# def run_backtest(priceHist, stopLoss: float = -10, maxHoldDay:int=40, shares: int = 1000):
#     res = {}
#     for tic, price in priceHist.items():
#         print(" Back testing '%s'" % tic)
#         if len(price['close']) > 100:
#             res[tic] = simple_MACD_RSI_backtest(price, stopLoss, maxHoldDay, shares)
    
#     # report
#     for k,v in res.items():
#         if v['winPerc'] > 0.6 and v['tradeCnt'] >= 4:
#             print("  %s - trade %0d win %0d (%0.2f%%) profit %0.2f (%0.2f%%) maxCap %0.2f maxHold %0d" % 
#                 (k, v['tradeCnt'], v['winCnt'], v['winPerc']*100, v['profit'], v['profitPerc']*100, v['maxCap'], v['maxDay']))
#             if v['buyNow']: print("        -----> BUY NOW")
#     return res

# Recheck all tickets, run this once a month to see any change in my brackets of strategy tickets
def recheckAll(strategyName: str, priceHist, stopLoss: float = -10, 
                maxHoldDay:int=20, shares: int = 1000, 
                report: bool = True, debug: bool = False):
    _G['DEBUG'] = debug
    res = {}
    for tic, price in priceHist.items():
        print(" Back testing '%s'" % tic)
        if len(price['close']) > 100:
            res[tic] = run_backtest(strategyName, price, stopLoss, maxHoldDay, shares)
    
    # report
    if report:
        for k,v in res.items():
            if v['winPerc'] > 0.6 and v['tradeCnt'] >= 4:
                print("  %s - trade %0d win %0d (%0.2f%%) profit %0.2f (%0.2f%%) maxCap %0.2f maxHold %0d" % 
                    (k, v['tradeCnt'], v['winCnt'], v['winPerc']*100, v['profit'], v['profitPerc']*100, v['maxCap'], v['maxDay']))
                if v['actionNow'] != "NONE": print("        -----> %s NOW" % v['actionNow'])
    return res

# Base on current good tickets & position to check for sigh of check
def getDecisionNow(strategyName: str):
    tickets = json.load(open('data/strategyMeta.json'))[strategyName]
    actCnt = 0
    print('Running strategy "%s" ... ' % strategyName)
    for tic in tickets:
        price = pd.DataFrame(StockAPI.getPriceHistory(tic, 365*2+50))
        # For testing, this is wher VNM recommended to BUY
        #price = pd.DataFrame(StockAPI.getPriceHistory(tic, 365*2+50, tillDate=datetime.datetime.strptime('28/01/2021 07:00', "%d/%m/%Y %H:%M")))
        # This is where VNM recommended SELL
        #price = pd.DataFrame(StockAPI.getPriceHistory(tic, 365*2+50, tillDate=datetime.datetime.strptime('01/09/2020 07:00', "%d/%m/%Y %H:%M")))
        res = run_backtest(strategyName, price)
        if res['actionNow'] != "NONE":
            print('  Stock %s now: %s' % (tic, res['actionNow']))
            actCnt += 1
    print("---- Finished checking for '%s'. There's action recommended for %0d/%0d" % (strategyName, actCnt, len(tickets)))

def getDecisionTest():
    prices = {}
    periods = 365*2+50
    for exc in ['hose', 'hnx']:
        print("Getting price for '%s' ..." % exc)
        tickets = StockAPI.getAllSymbols('hose')
        for tic in tickets:
            if tic in prices: print("DUPLICATED SYMBOLS??? %s" % tic)
            prices[tic] = pd.DataFrame(StockAPI.getPriceHistory(tic, periods))
            # macdHist = si.ma_convergence_divergence(ps)['hist']
            # rsi = si.relative_strength_index(ps)

            # print(tic, prices[tic].head(), len(prices[tic]['close']))
            if len(prices[tic]['close']) < 200:
                # print("[%s] too short history -> skiped" % tic)
                continue
            volMa = si.simple_moving_average(prices[tic]['volumn'], 10)
            if volMa.iloc[-1] < 50000:
                # print("[%s] Too low volumn -> skipped " % tic)
                continue

            ema50 = si.exponential_moving_average(prices[tic]['close'], 50)
            ema21 = si.exponential_moving_average(prices[tic]['close'], 21)
            ema14 = si.exponential_moving_average(prices[tic]['close'], 14)

            dec, reason = simple_moving_average_decision(ema50, ema21, ema14)
            if dec != Decision.KEEP:
                print(" --- %s -> %s" % (tic, dec))
