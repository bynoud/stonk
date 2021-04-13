
from enum import Enum
from Symbol import SymbolHistory
import StockAPI
import logging

Decision = Enum('Decision', 'BUY SELL UNKN KEEP NONE')
Trend = Enum('Trend', 'BULL BEAR NONE')

class BacktestResult:
    def __init__(self):
        self.maxCap = -1
        self._combineProfit = 0.0
        self._winProfit = 0.0
        self._lossProfit = 0.0
        self.winCnt = 0
        self.tradeCnt = 0
        self.maxDay = 0
        self.actionNow = 'NONE'

    @property
    def winPerc(self):
        return 0.0 if (self.tradeCnt==0) else float(self.winCnt)*100.0 / self.tradeCnt
    @property
    def combineProfit(self):
        return 0.0 if (self.tradeCnt==0) else float(self._combineProfit)*100.0 / self.tradeCnt
    @property
    def winProfit(self):
        return 0.0 if (self.winCnt==0) else float(self._winProfit)*100.0 / self.winCnt
    @property
    def lossProfit(self):
        lossCnt = self.tradeCnt - self.winCnt
        return 0.0 if (lossCnt==0) else float(self._lossProfit)*100.0 / lossCnt

    def addCap(self, cap):
        if cap > self.maxCap: self.maxCap = cap

    def addTrade(self, buyPrice, sellPrice, holdDay):
        diffPrice = sellPrice - buyPrice
        diffPerc = float(diffPrice) / buyPrice
        self._combineProfit += diffPerc
        self.tradeCnt += 1
        if diffPrice > 0:
            self.winCnt += 1
            self._winProfit += diffPerc
        else:
            self._lossProfit += diffPerc
        if holdDay > self.maxDay:
            self.maxDay = holdDay

    def report(self):
        print("Total Trade: %0d (maxCap %0.2f) Win %0d (%0.2f) profit/trade %0.2f%% (W %0.2f%% L %0.2f%%)" % (
            self.tradeCnt, self.maxCap, self.winCnt, self.winPerc,
            self.combineProfit, self.winProfit, self.lossProfit
        ))



def run_backtest(symbol: SymbolHistory, decisionFunc,
                 minHoldDay:int=2, stopLoss: float = -10.0,
                 maxHoldDay:int=40, shares: int = 1000,
                 debug: bool = False, **funcParams) -> BacktestResult:
    buyPrice = 0.0
    buyIdx = -1
    result = BacktestResult()
    print("XXX %s %s %s %s" % (symbol.name, decisionFunc.__name__, funcParams.keys(), debug))

    # logging.debug("Runing Backtest for '%s' with '%s(%s)'" % (symbol.name, decisionFunc.__name__, funcParams))
    if debug: print("Runing Backtest for '%s' with '%s(%s)'" % (symbol.name, decisionFunc.__name__, funcParams.keys()))
    maxIdx = symbol.len-1
    for idx in range(50, maxIdx+1):
        if idx - buyIdx < minHoldDay: continue

        dec, reason = Decision.NONE, ""
        if buyIdx >= 0:
            # Stop loss
            loss = symbol.close[idx] - buyPrice
            loss = float(loss) * 100.0 / buyPrice
            if loss < stopLoss:
                dec, reason = Decision.SELL, "Stop loss @%d (%0.2f)" % (symbol.close[idx], loss)
            # Too long, just go out
            if idx - buyIdx >= maxHoldDay:
                dec, reason = Decision.SELL, "Is keeping more than %d periods" % (idx-buyIdx)

        if dec == Decision.NONE:
            dec, reason = decisionFunc(**funcParams, idx=idx)

        # print("XX2 %d maxIdx %d buyId %d %s %s " % (idx, maxIdx, buyIdx, dec, reason))

        if dec == Decision.BUY:
            if idx == maxIdx:
                result.actionNow = "BUY"
                # logging.debug("[%s] BUY NOW [%0d] @ %0.3f '%s'" % (symbol.name, idx, buyPrice, reason))
                if debug: print("[%s] BUY NOW [%0d] @ %0.3f '%s'" % (symbol.name, idx, buyPrice, reason))
            else:
                if buyIdx > 0:
                    # already in position
                    # logging.debug("[%s] BUY indicate when already in position '%s'" % (symbol.name, reason))
                    if debug: print("[%s] BUY [%0d] indicate when already in position '%s'" % (symbol.name, idx, reason))
                    pass
                else:
                    buyIdx = idx+1
                    buyPrice = symbol.open[buyIdx]
                    result.addCap(buyPrice * shares)
                    # logging.debug("[%s] BUY [%0d] @ %0.3f '%s'" % (symbol.name, idx, buyPrice, reason))
                    if debug: print("[%s] BUY [%0d] @ %0.3f '%s'" % (symbol.name, idx, buyPrice, reason))
        elif dec == Decision.SELL:
            if idx == maxIdx:
                result.actionNow = "SELL"
                # logging.debug("[%s] SELL NOW [%0d] @ %0.3f '%s'" % (symbol.name, idx, buyPrice, reason))
                if debug: print("[%s] SELL NOW [%0d] @ %0.3f '%s'" % (symbol.name, idx, buyPrice, reason))
            else:
                if buyIdx < 0:
                    # Not in position
                    # logging.debug("[%s] SELL indicate when not in position '%s'" % (symbol.name, reason))
                    if debug: print("[%s] SELL [%0d] indicate when not in position '%s'" % (symbol.name, idx, reason))
                    pass
                else:
                    result.addTrade(buyPrice, symbol.open[idx+1], idx+1 - buyIdx)
                    buyIdx = -1
                    if debug: print("[%s] SELL [%0d] @ %0.3f '%s'" % (symbol.name, idx, buyPrice, reason))
        
    return result

def getBestResult(results):
    maxWin = 0.0
    maxRes = None
    for res in results:
        if res['res'].winPerc > maxWin:
            maxWin = res['res'].winPerc
            maxRes = res
    return maxRes
    