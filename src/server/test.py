
# # # run this : exec(open("test.py").read())

def get_signal_now(self):
    import HeikinAshiStrategy
    from StrategyCommon import Decision
    res = []
    for tic, sym in self._symbols.items():
        dec, reason = HeikinAshiStrategy.heikin_ashi_stochrsi_decision(
            ha=sym.heikin_ashi(), rsi=sym.rsi(), ma5=sym.ema(5), ma10=sym.ema(10)
        )
        if dec != Decision.NONE:
            # print("[%s] --->>> BUY (%s)" % (tic, reason))
            res.append({'tic':tic, 'dec':dec, 'reason':reason})

    for k,v in self._intra.items():
        if len(v) == 0:
            continue
        averVol = self._symbols[k].sma(src='volumn', window=50).iloc[-1]
        try:
            buyVol, sellVol = v['b'].sum(), v['s'].sum()
        except Exception as e:
            print("FAILED", e, v)
        if buyVol >= sellVol and ( (buyVol + sellVol) / averVol ) >= 1.5:
            buyPrice = (v['b'] * v['p']).sum() / buyVol
            sellPrice = (v['s'] * v['p']).sum() / sellVol
            if buyPrice >= sellPrice:
                # print("[%s] --->>> Strong Money flow" % k)
                res.append({'tic':k, 'dec':Decision.BUY, 'reason':'Strong Money flow'})

    self._signals = res
    return res

# import pickle
# import StrategySession
# import HeikinAshiStrategy
# # prices = pickle.load(open('data/priceHistory2Years50.pkl', 'rb'))
# # ss = StrategySession.BacktestSession(priceHist=prices)
# ss = StrategySession.BacktestSession(fromFile='data/priceHistory2Years50_20202703.pkl')
# ss.start(lambda x: x.len>=200 and x.sma(src='volumn',window=90).iloc[-1] > 100000)
# ss.get_signal_now()

# # ss._tickets = ['FPT']
# # sym = ss._symbols['FPT']
# # res = ss.run_backtest(HeikinAshiStrategy.heikin_ashi_stochrsi_decision, 
# #     ha=sym.heikin_ashi(), rsi=sym.rsi(), ma5=sym.ema(5), ma10=sym.ema(10),
# #     debug=True)

# # import pickle, logging
# # from importlib import reload
# # import MovingAverageStrategy, StrategyCommon
# # logging.basicConfig(level='INFO')
# # priceHist = pickle.load(open('data/symbolHistory.pkl', 'rb'))
# # # bestMa = MovingAverageStrategy.check_best_match_ma(priceHist['VNM'])
# # # print(bestMa)

# # # res = StrategyCommon.run_backtest(priceHist['VNM'], MovingAverageStrategy.sma_psar_decision, {'long':15, 'short':7})

# # bestSma = MovingAverageStrategy.check_best_match_sma(priceHist['VNM'])
# # import pandas as pd
# # from Symbol import SymbolHistory
# # import Indicator

# # def double_ma_retrace(maLong, maShort, price):
# #     maDiff = maShort - maLong
# #     priceDiff = {}
# #     _diff = {}
# #     priceDiff[3] = price.diff(3).shift(-3) # On T3, check for different with T0 price
# #     priceDiff[4] = price.diff().shift(-4) # diff between T3 & T4
# #     priceDiff[5] = price.diff().shift(-5)
# #     _diff[3] = priceDiff[3] # If stop at T3, mean T3 is negative, save this negative as result
# #     _diff[4] = _diff[3] # if stop as T4, save T3 diff as result
# #     _diff[5] = price.diff(4).shift(-4) # if stop as T5, save T4 as result
# #     _diff[6] = price.diff(5).shift(-5) # if stop as T6, save T5 as result
# #     res = {'gold':[], 'death':[]}
# #     for idx in range(30, len(price)-5):
# #         if maDiff[idx-1] <= 0 and maDiff[idx] > 0:
# #             # look ahead to confirm the price
# #             for p in range(3,6):
# #                 if priceDiff[p][idx] < 0:
# #                     res['gold'].append([idx, p-1, _diff[p][idx]])
# #                     break
# #             else:
# #                 # No break, so no negative is found
# #                 res['gold'].append([idx, 5, _diff[6][idx]])
# #         if maDiff[idx-1] >= 0 and maDiff[idx] < 0:
# #             for p in range(3,6):
# #                 if priceDiff[p][idx] > 0:
# #                     res['death'].append([idx, p-1, _diff[p][idx]])
# #                     break
# #             else:
# #                 # No break, so no negative is found
# #                 res['death'].append([idx, 5, _diff[6][idx]])
# #     return {'gold': pd.DataFrame( 
# #                  {'diff': [x[2]*3 if x[1]<3 else x[2] for x in res['gold']], # punish for failed signal more by *3
# #                   't': [x[1] for x in res['gold']],
# #                   'idx': [x[0] for x in res['gold']]}),
# #           'death': pd.DataFrame( 
# #                  {'diff': [x[2]*3 if x[1]<3 else x[2] for x in res['death']],
# #                   't': [x[1] for x in res['death']],
# #                   'idx': [x[0] for x in res['death']]} )}
    
# # def double_ma_list(shortWinLimit=[5,14], maxWin=80):
# #     res = []
# #     for sw in range(shortWinLimit[0],shortWinLimit[1]+1):
# #         for lw in range(min(int(sw*1.5), maxWin), min(int(sw*3), maxWin)+1):
# #             if [lw,sw] not in res:
# #                 res.append([lw,sw])
# #     return res

# # def triple_ma_list(shortWinLimit=[5,14], maxWin=80):
# #     res = []
# #     for sw in range(shortWinLimit[0],shortWinLimit[1]+1):
# #         for mw in range(min(int(sw*1.5), maxWin), min(int(sw*2.5), maxWin)+1):
# #             for lw in range(min(int(mw*1.5), maxWin), min(int(mw*2.5), maxWin)+1):
# #                 if [lw,mw,sw] not in res:
# #                     res.append([lw,mw,sw])
# #     return res

# # def get_best_double_ma(symbol: SymbolHistory, func=None, filter=True):
# #     print("Finding the best match for Double MA of '%s' ..." % symbol.name, end='', flush=True)
# #     res = []
# #     cnt = 20
# #     price = Indicator.exponential_moving_average(symbol.close,6).shift(-3) # this is better to indicate the trend on some next day
# #     if func is None: func = symbol.sma
# #     for lw,sw in double_ma_list():
# #         maShort = func(sw)
# #         maLong = func(lw)
# #         trace = double_ma_retrace(maLong, maShort, price)
# #         res.append({'win':[lw,sw], 
# #                 'gold': [trace['gold']['diff'].mean().round(2), trace['gold']['diff'].std().round(2),
# #                      trace['gold']['t'].mean().round(2), trace['gold']['t'].std().round(2)],
# #             'death': [trace['death']['diff'].mean().round(2), trace['death']['diff'].std().round(2),
# #                      trace['death']['t'].mean().round(2), trace['death']['t'].std().round(2)],})
# #         cnt -= 1
# #         if cnt == 0:
# #             print('.', end='', flush=True)
# #     print(" Done")
    
# #     if filter:
# #         best = res[0]
# #         for r in res:
# #             if r['gold'][0] >= best['gold'][0] and r['gold'][2] >= 3:
# #                 ok = True
# #                 if r['gold'][0] == best['gold'][0]:
# #                     if r['gold'][1] < best['gold'][1]:
# #                         ok = False # std of Gold is smaller, dont take it
# #                     elif r['death'][0] > best['death'][0]:
# #                         ok = False # negative is smaller
# #                 if ok:
# #                     best = r
# #         return best
# #     else:
# #         return res

