
import pickle
import pandas as pd
import StockAPI
from Symbol import SymbolHistory, getAllSymbolHistory
from StrategyCommon import run_backtest, Decision
from MovingAverageStrategy import get_best_double_ma
import MoneyFlowStrategy
import HeikinAshiStrategy
import Signal
import StockDB

# def getAllSymbolHistory(dayNum:int=365*2+50, tickets=None, exchange: str = 'HOSE HNX'):
#     if tickets is None:
#         tickets = StockAPI.getAllTickets(exchange)
#     print("Getting price history of %d Stocks ..." % len(tickets), end="", flush=True)
#     price = {}
#     cnt = 10
#     for tic in tickets:
#         symbol = SymbolHistory(tic, StockAPI.getPriceHistory(tic, dayNum))
#         price[tic] = symbol
#         cnt -= 1
#         if cnt == 0:
#             print(".", end="", flush=True)
#             cnt = 10
#     print(" Done")
#     return price

def _process_intra(intra):
    v = intra
    buy = {}
    sell = {}
    for r in v:
        p = r['Price']
        if p not in buy: buy[p] = 0
        if p not in sell: sell[p] = 0
        if r['IsBuy']:
            buy[p] += r['Vol']
        else:
            sell[p] += r['Vol']
    prices = sorted(buy.keys())
    return pd.DataFrame({
        'p': prices,
        'b': [buy[p] for p in prices],
        's': [sell[p] for p in prices],
    })

class BacktestSession:
    def __init__(self, tickets=None, debug=False, refetchAll=False):
        self._tickets = tickets
        self._symbols = None
        # self._db = StockDB.StockDB()
        # self._intra = None
        self._signals = None
        self.debugMode = debug
        if debug:
            self._symbols = pickle.load(open('data/current_prices.pkl', 'rb'))
            print('symbols', len(self._symbols))
            # self._signals = pickle.load(open('data/current_signals.pkl', 'rb'))
            # self._intra = pickle.load(open('data/current_intra.pkl', 'rb'))
        if tickets is None and (debug or not refetchAll):
            self._tickets = pickle.load(open('data/selTickets.pkl', 'rb'))
            print('tickets', len(self._tickets))

    def backup_price(self, filename):
        pickle.dump(self._symbols, open(filename, 'wb'))

    def start(self, filerFunc='_default_'):
        refilter = False
        if self._tickets is None:
            self._tickets = StockAPI.getAllTickets('hose hnx upcom')
            refilter = True
        if self._symbols is None:
            self._symbols = getAllSymbolHistory(tickets=self._tickets)

        if refilter and filerFunc is not None:
            if filerFunc == '_default_':
                # filerFunc = lambda(x: x.len>=100 and x.sma(src='volumn',window=50).iloc[-1]>=100000)
                def _defaultFilter(x):
                    return (
                        x.len>=100 and 
                        x.sma(src='volumn',window=50).iloc[-1]>=200000 and 
                        2.0 < x.close.iloc[-1] < 110 and
                        len(x.name) == 3 # To remove Derative ticket...
                    )
                filerFunc = _defaultFilter
            self._symbols = {x.name:x for x in filter(filerFunc, self._symbols.values())}
            self._tickets = sorted(self._symbols.keys())
        pickle.dump(self._symbols, open('data/current_prices.pkl', 'wb'))
        pickle.dump(self._tickets, open('data/selTickets.pkl', 'wb'))
        # # get Intra
        # if self._intra is None:
        #     self._intra = StockAPI.getIntradayBooks(self._tickets)
        #     if not self.debugMode:
        #         self._db.add_intraday(self._intra)
        if not self.debugMode:
            StockAPI.fetchIntradayAllSymbols(self._symbols, pastDays=100)
        # pickle.dump(self._intra, open('data/current_intra.pkl', 'wb'))
        print('len', len(self._tickets), len(self._symbols))
    
    def end(self):
        pass
        # self._db.close()

    # def _process_intra(self):
    #     print("Process intra")
    #     res = {}
    #     for k,v in self._intra.items():
    #         if k not in self._symbols:
    #             continue
    #         buy = {}
    #         sell = {}
    #         for r in v:
    #             p = r['Price']
    #             if p not in buy: buy[p] = 0
    #             if p not in sell: sell[p] = 0
    #             if r['IsBuy']:
    #                 buy[p] += r['Vol']
    #             else:
    #                 sell[p] += r['Vol']
    #         prices = sorted(buy.keys())
    #         yield (k, pd.DataFrame({
    #             'p': prices,
    #             'b': [buy[p] for p in prices],
    #             's': [sell[p] for p in prices],
    #         }))

    def run_backtest(self, strategyFunc, **params):
        res = {}
        print("Running backtest '%s(%s)' for %d tickets", strategyFunc.__name__, params.keys(), len(self._tickets))
        for tic in self._tickets:
            res[tic] = run_backtest(self._symbols[tic], strategyFunc, **params)
        return res

    def check_best_match_double_ma(self, ignores=None):
        if ignores is None: ignores = {}
        res = {}
        for tic in self._tickets:
            if tic in ignores:
                continue
            smaBest = get_best_double_ma(self._symbols[tic])
            emaBest = get_best_double_ma(self._symbols[tic], self._symbols[tic].ema)
            if smaBest['gold'][0] <= 0 and emaBest['gold'][0] <= 0:
                win = 'None', None
            elif smaBest['gold'][0] <= 0:
                win = 'sma', emaBest['win']
            if  emaBest['gold'][0] > smaBest['gold'][0]:
                win = 'ema', emaBest['win']
            else:
                win = 'sma', smaBest['win']
            res[tic] = win
        return res

    def retrain(self, incr=True):
        try:
            curMeta = pickle.load(open('data/meta.pkl', 'rb'))
        except FileNotFoundError:
            curMeta = {}
        newMeta = {}
        newMeta['doubleMA'] = self.check_best_match_double_ma(list(curMeta.keys()) if incr else None)

        pickle.dump(newMeta, open('data/meta.pkl', 'wb'))
        return newMeta

    def getSignal(self):
        for tic, sym in self._symbols.items():
            if Signal.is_near_super_trend_support(sym):
                print("[%s] It trading near SuperTrend Support # %0.2f" % (tic, sym.close.iloc[-1]))

    def get_signal_now(self):
        res = {}
        
        # self._hakinAshiRsi(res)

        # self._moneyInout(res)

        self._moneyFlow(res)

        # self._onStable(res)

        self._signals = res
        pickle.dump(res, open('data/current_signals.pkl', 'wb'))
        return res

    def _hakinAshiRsi(self, res):
        for tic, sym in self._symbols.items():
            dec, reason = HeikinAshiStrategy.heikin_ashi_stochrsi_decision(
                ha=sym.heikin_ashi(), rsi=sym.rsi(), ma5=sym.ema(5), ma10=sym.ema(10)
            )
            if dec != Decision.NONE:
                # print("[%s] --->>> BUY (%s)" % (tic, reason))
                try:
                    res[tic].append({'dec':dec, 'reason':reason})
                except:
                    res[tic] = [{'dec':dec, 'reason':reason}]
                # res.append({'tic':tic, 'dec':dec, 'reason':reason})

            # RSI
            rsi = sym.rsi()
            if rsi.iloc[-2] < 30 and rsi.iloc[-1] > rsi.iloc[-2]:
                try:
                    res[tic].append({'dec':Decision.BUY, 'reason':'RSI<30 but in recover'})
                except:
                    res[tic] = [{'dec':Decision.BUY, 'reason':'RSI<30 but in recover'}]

    # def _moneyInout(self, res):
    #     for k,v in self._process_intra():
    #         if len(v) == 0:
    #             continue
    #         averVol = self._symbols[k].sma(src='volumn', window=50).iloc[-1]
    #         buyVol, sellVol = v['b'].sum(), v['s'].sum()
    #         if ( (buyVol + sellVol) / averVol ) >= 1.5:
    #             buyPrice = (v['b'] * v['p']).sum() / buyVol
    #             sellPrice = (v['s'] * v['p']).sum() / sellVol
    #             if buyVol >= sellVol and buyPrice >= sellPrice:
    #                 # print("[%s] --->>> Strong Money flow" % k)
    #                 res.append({'tic':k, 'dec':Decision.BUY, 'reason':'Strong Money flow'})
    #             if buyVol < sellVol and buyPrice < sellPrice:
    #                 res.append({'tic':k, 'dec':Decision.SELL, 'reason':'Strong Money withdraw'})

    def _moneyFlow(self, res):
        money = MoneyFlowStrategy.checkMoneyFlowAll(self._symbols)
        for tic,r in money.items():
            if r is None:
                continue
            cnt = 0
            for x in r[0]:
                if x != '':
                    cnt += 1
            if cnt > 0:
            # if r[0][-3] != '' or r[0][-2] != '' or r[0][-1] != '':
                try:
                    res[tic].append({'dec': Decision.BUY, 'reason':r[0]})
                except:
                    res[tic] = [{'dec': Decision.BUY, 'reason':r[0]}]

    def _onStable(self, res):
        money = MoneyFlowStrategy.onStableAll(self._symbols)
        for tic,r in money.items():
            if r is None:
                continue
            cnt = 0
            for x in r[0]:
                if x != '':
                    cnt += 1
            if cnt > 0:
            # if r[0][-3] != '' or r[0][-2] != '' or r[0][-1] != '':
                try:
                    res[tic].append({'dec': Decision.BUY, 'reason':r[0]})
                except:
                    res[tic] = [{'dec': Decision.BUY, 'reason':r[0]}]

    def get_halfsession_signal(self):
        res = {}
        if self._signals is None:
            print("**ERROR: previous session is not started yet")
        tickets = sorted(self._signals.keys())
        money = MoneyFlowStrategy.checkMoneyFlowAll([self._symbols[x] for x in tickets], halfsess=True)
        for tic,r in money.items():
            if r is None:
                continue
            cnt = 0
            for x in r[0]:
                if x != '':
                    cnt += 1
            if cnt > 3 or r[0][-1] != '':
                try:
                    res[tic].append({'dec': Decision.BUY, 'reason':r[0]})
                except:
                    res[tic] = [{'dec': Decision.BUY, 'reason':r[0]}]
        return res

    @property
    def signals(self):
        if self._signals == None:
            self.get_signal_now()
        return self._signals
        
# for k,v in res.items():
#     if k not in ss._symbols:
#         continue
#     averVol = ss._symbols[k].sma(src='volumn', window=50).iloc[-1]
#     buyVol, sellVol = v['b'].sum(), v['s'].sum()
#     if buyVol >= sellVol and ( (buyVol + sellVol) / averVol ) >= 1.5:
#         buyPrice = (v['b'] * v['p']).sum() / buyVol
#         sellPrice = (v['s'] * v['p']).sum() / sellVol
#         if buyPrice >= sellPrice:
#             print("[%s] --->>> Strong Money flow" % k)
