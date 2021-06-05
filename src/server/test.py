
# # # # run this : exec(open("test.py").read())
# import requests, datetime, json
# import pandas as pd
# import numpy as np

# class Error(Exception):
#     pass

# def intraMatchedOnly(df):
#     return df[df['mt'] != df['mt'].shift(1)].reset_index()
    
# def _intraProcess(df, ceil, floor):
#     df = df.loc[(df['mt']==0).idxmin():].reset_index() # drop ATO phase
#     # sel = df[df['mt'] != df['mt'].shift(1)].reset_index()  # only check where total matched is changed
#     df1 = df.shift(1)
#     for i in range(1,4):
#         df.loc[(df['op%d'%i]==0) & (df['ov%d'%i] > 0), ['op%d'%i]] = floor
#         df.loc[(df['bp%d'%i]==0) & (df['bv%d'%i] > 0), ['bp%d'%i]] = ceil

#     df['buy'] = pd.Series(0, index=df.index)
#     df.loc[df['mp'] >= df1['op1'], ['buy']] = 1
#     df.loc[(df['mp'] < df1['op1']) & (df['mp'] > df1['bp1']), ['buy']] = -1 # unknow direction

#     # at ATO
#     sel = df.iloc[0]
#     sel['buy'] = 1 if sel['mp'] >= sel['op1'] else 0 if sel['mp'] <= sel['bp1'] else -1

#     # at ATC
#     sel = df.iloc[-1]
#     sel['buy'] = 1 if sel['mp'] >= sel['op1'] else 0 if sel['mp'] <= sel['bp1'] else -1

#     # # # There's always a 'mt' = 0, right? if not, inform me
#     # # if sel[0]['mt'] != 0:
#     # #     raise Error("The intra has first item is not 0. Check this case")

#     # # First time matched
#     # lrow = sel.loc[0]
#     # sel['buy'].at[1] = 1 if lrow['mp'] >= lrow['op1'] else 0 if lrow['mp'] <= lrow['bp1'] else -1

#     # for i,row in sel[1:].iterrows():
#     #     # print(row)
#     #     if row['mp'] <= lrow['bp1']:
#     #         sel['buy'].at[i] = 0
#     #     elif row['mp'] < lrow['op1']:
#     #         # raise Error("Matched price is in the middle of last best [%d] %f <> %f - %f" % (i, row['mp'], lrow['bp1'], lrow['op1']))
#     #         sel['buy'].at[i] = -1 # sometime, the lagging on updating table cause the matched price is in the middle of previous best
#     #     lrow = row
    
#     # # The last (normally is ATC)
#     # # print(lrow)
#     # sel['buy'].at[-1] = 1 if lrow['mp'] >= lrow['op1'] else 0 if lrow['mp'] <= lrow['bp1'] else -1
    
#     return df

# def intradaySearch_vdsc(tickets,date=''):
#     if date == '': date = datetime.datetime.now().strftime("%d/%m/%Y")
#     print('date', date)
#     url = 'https://livedragon.vdsc.com.vn/general/intradaySearch.rv'
#     r = requests.get(url)
#     if r.status_code != 200:
#         raise Error('Failed to get "%s"' % url)
#     ck = r.headers['Set-Cookie']
#     res = {}
#     for tic in tickets:
#         r = requests.post(url, 
#             data={'stockCode':tic, 'boardDate': date},
#             headers={'Cookie':ck}
#         )
#         if r.status_code != 200:
#             raise Error('Failed to get Intra for "%s": %s' % (tic, r.reason))
#         txt = r.content.decode('utf-8')
#         if txt == '':
#             res[tic] = None
#         else:
#             try:
#                 j = json.loads(txt)
#             except json.decoder.JSONDecodeError:
#                 raise Error('Failed to decode Intra for "%s": %s' % (tic, txt))
#             if not j['success']:
#                 raise Error('Server return failed for Intra "%s": %s' % (tic, j['message']))
#             intra = pd.DataFrame(index=range(len(j['list'])),
#                 columns='mp mv mt time ov1 ov2 ov3 op1 op2 op3 bv1 bv2 bv3 bp1 bp2 bp3'.split())
#             for i,v in enumerate(j['list']):
#                 intra.at[i] = {
#                     'time': v['TradeTime'],
#                     'mp': v['MatchedPrice'], 'mv': v['MatchedVol'], 'mt': v['MatchedTotalVol'],
#                     'ov1': v['OfferVol1'], 'ov2': v['OfferVol2'], 'ov3': v['OfferVol3'],
#                     'op1': v['OfferPrice1'], 'op2': v['OfferPrice2'], 'op3': v['OfferPrice3'],
#                     'bv1': v['BidVol1'], 'bv2': v['BidVol2'], 'bv3': v['BidVol3'],
#                     'bp1': v['BidPrice1'], 'bp2': v['BidPrice2'], 'bp3': v['BidPrice3'],
#                 }
#             res[tic] = _intraProcess(intra)
#     return res

# def _getCookie():
#     # print('date', date)
#     r = requests.get('http://priceboard1.vcsc.com.vn/vcsc/intraday')
#     if r.status_code != 200:
#         raise Error('Failed to get')
#     return r.headers['Set-Cookie']

# def intradaySearch(tic, date, cookie=''):
#     if cookie == '':
#         cookie = _getCookie()
#     # print('Se', tic, date, cookie)
#     r = requests.post('http://priceboard1.vcsc.com.vn/vcsc/IntradayDataAjaxService?time=%d' % datetime.datetime.now().timestamp(), 
#         data={'data': '{"command":"init","msgid":1,"data":["%s","%s"]}' % (tic, date)},
#         headers={'Cookie':cookie, 
#             'Host':'priceboard1.vcsc.com.vn', 
#             'Origin':'http://priceboard1.vcsc.com.vn',
#             'Referer':'http://priceboard1.vcsc.com.vn/vcsc/intraday'}
#     )
#     if r.status_code != 200:
#         raise Error('Failed to get Intra for "%s": %s' % (tic, r.reason))
#     txt = r.content.decode('utf-8')
#     if txt == '':
#         # print('It empty return')
#         return None

#     try:
#         j = json.loads(txt)
#     except json.decoder.JSONDecodeError:
#         raise Error('Failed to decode Intra for "%s": %s' % (tic, txt))
#     # if not j['success']:
#     #     raise Error('Server return failed for Intra "%s": %s' % (tic, j['message']))
#     if len(j['content']) == 0:
#         # print("It empty content '%s'" % j)
#         return None

#     intra = pd.DataFrame(index=range(len(j['content'])),
#         columns='mp mv mt time ov1 ov2 ov3 op1 op2 op3 bv1 bv2 bv3 bp1 bp2 bp3'.split())
#     def v2i(s):
#         return int(s.replace(',','')) * 10
#     def p2f(s):
#         return 0.0 if (s in ['ATC', 'ATO']) else float(s)
#     ceil, floor = p2f(j['content'][0]['cei']), p2f(j['content'][0]['flo'])
#     for i,v in enumerate(j['content']):
#         intra.at[i] = {
#             'time': v['time'],
#             'mp': float(v['mat']), 'mv': v2i(v['mvo']), 'mt': v2i(v['tmv']),
#             'ov1': v2i(v['sv1']), 'ov2': v2i(v['sv2']), 'ov3': v2i(v['sv3']),
#             'op1': p2f(v['sp1']), 'op2': p2f(v['sp2']), 'op3': p2f(v['sp3']),
#             'bv1': v2i(v['bv1']), 'bv2': v2i(v['bv2']), 'bv3': v2i(v['bv3']),
#             'bp1': p2f(v['bp1']), 'bp2': p2f(v['bp2']), 'bp3': p2f(v['bp3']),
#         }
#     return _intraProcess(intra, ceil, floor)

# def intradaySearchAllTickets(tickets,date=None):
#     date = datetime.datetime.now().strftime("%Y%m%d")
#     # print('date', date)
#     cookie = _getCookie()
#     res = {}
#     for tic in tickets:
#         res[tic] = intradaySearch(tic, date, cookie)
#     return res

# def getIntradayHistory(ticket, dayNum=365*2+50):
#     import StockAPI
#     dates = StockAPI.getTradingDate(dayNum)
#     res = {}
#     print('Getting Intra History of "%s" ...' % ticket, end='', flush=True)
#     cnt = 10

#     # while retry > 0:
#     cookie = _getCookie()
#     failed = 0
#     for i in range(len(dates)-1, -1, -1):
#         dateStr = datetime.datetime.fromtimestamp(dates[i]).strftime("%Y%m%d")
#         intra = intradaySearch(ticket, dateStr, cookie)
#         if intra is None:
#             failed += 1
#             if failed > 5: # result for some day may not avaiable?!?
#                 break # no more result available
#         res[dates[i]] = intra
#         cnt -= 1
#         if cnt <= 0:
#             print('.',end='',flush=True)
#             cnt = 10
#     print('Done')
#     return res

# def get_signal_now(self):
#     import HeikinAshiStrategy
#     from StrategyCommon import Decision
#     res = []
#     for tic, sym in self._symbols.items():
#         dec, reason = HeikinAshiStrategy.heikin_ashi_stochrsi_decision(
#             ha=sym.heikin_ashi(), rsi=sym.rsi(), ma5=sym.ema(5), ma10=sym.ema(10)
#         )
#         if dec != Decision.NONE:
#             # print("[%s] --->>> BUY (%s)" % (tic, reason))
#             res.append({'tic':tic, 'dec':dec, 'reason':reason})

#     for k,v in self._intra.items():
#         if len(v) == 0:
#             continue
#         averVol = self._symbols[k].sma(src='volumn', window=50).iloc[-1]
#         try:
#             buyVol, sellVol = v['b'].sum(), v['s'].sum()
#         except Exception as e:
#             print("FAILED", e, v)
#         if buyVol >= sellVol and ( (buyVol + sellVol) / averVol ) >= 1.5:
#             buyPrice = (v['b'] * v['p']).sum() / buyVol
#             sellPrice = (v['s'] * v['p']).sum() / sellVol
#             if buyPrice >= sellPrice:
#                 # print("[%s] --->>> Strong Money flow" % k)
#                 res.append({'tic':k, 'dec':Decision.BUY, 'reason':'Strong Money flow'})

#     self._signals = res
#     return res

# def dump(filename, intra, symbol, dates):
#     chg = symbol.close.diff() / symbol.close
#     with open(filename, 'w') as fp:
#         fp.write('date\thigh\tlow\topen\tclose\tbuyVol\tbuySum\tsellVol\tsellVol')
#         for i in range(len(dates)-1, 0, -1):
#             date = dates[i]
#             s = '%s\t' % datetime.datetime.fromtimestamp(dates[i]).strftime('%Y%m%d')
#             # print(i)
#             s += '%s\t%s\t%s\t%s\t%s\t' % (symbol.high[i], symbol.low[i], symbol.open[i], symbol.close[i], '')
#             intr = intra[i]
#             buyVol, sellVol = 1.0, 1.0
#             buySum, sellSum = 1.0, 1.0
#             bidVol, askVol = 1, 1
#             bidPrice, buyPrice = 1, 1
#             sellPrice, askPrice = 1, 1

#             if intr is not None:
#                 unk = intr[intr['buy']==-1]
#                 if (float(len(unk)) / len(intr)) > 0.3:
#                     print('Intra is too inconsistence to consider', symbol.name, len(unk), len(intr), datetime.datetime.fromtimestamp(date))
#                 else:
#                     sidePower = checkIntraSidePower(intr)
#                     res = sidePower[0]
#                     buyVol, sellVol = res['buy'].sum(), res['sell'].sum()
#                     bidVol, askVol = res['bid'].sum(), res['ask'].sum()
#                     buySum, sellSum = (res['buy'] * res['price']).sum(), (res['sell'] * res['price']).sum()
#                     # bidPrice = (res['bid'] * res['price']).sum() / res['bid'].sum()
#                     # buyPrice = (res['buy'] * res['price']).sum() / res['buy'].sum()
#                     # sellPrice = (res['sell'] * res['price']).sum() / res['sell'].sum()
#                     # askPrice = (res['ask'] * res['price']).sum() / res['ask'].sum()

#                     # intr = intraMatchedOnly(intr)
#                     # buy = intr[intr['buy']==1]
#                     # sell = intr[intr['buy']==0]
#                     # buyVol, sellVol = buy['mv'].sum(), sell['mv'].sum()
#                     # buySum, sellSum = (buy['mv'] * buy['mp']).sum(), (sell['mv'] * sell['mp']).sum()

#             s += '%s\t%s\t%s\t%s\t' % (buyVol, buySum, sellVol, sellSum)
#             s += '%s\t%s\t%s\t%s\t' % (bidVol, askVol, bidPrice, askPrice)
#             fp.write('%s\n' % s)

# # import pickle
# # import StrategySession
# # import HeikinAshiStrategy
# # # prices = pickle.load(open('data/priceHistory2Years50.pkl', 'rb'))
# # # ss = StrategySession.BacktestSession(priceHist=prices)
# # ss = StrategySession.BacktestSession(fromFile='data/priceHistory2Years50_20202703.pkl')
# # ss.start(lambda x: x.len>=200 and x.sma(src='volumn',window=90).iloc[-1] > 100000)
# # ss.get_signal_now()

# # # ss._tickets = ['FPT']
# # # sym = ss._symbols['FPT']
# # # res = ss.run_backtest(HeikinAshiStrategy.heikin_ashi_stochrsi_decision, 
# # #     ha=sym.heikin_ashi(), rsi=sym.rsi(), ma5=sym.ema(5), ma10=sym.ema(10),
# # #     debug=True)

# # # import pickle, logging
# # # from importlib import reload
# # # import MovingAverageStrategy, StrategyCommon
# # # logging.basicConfig(level='INFO')
# # # priceHist = pickle.load(open('data/symbolHistory.pkl', 'rb'))
# # # # bestMa = MovingAverageStrategy.check_best_match_ma(priceHist['VNM'])
# # # # print(bestMa)

# # # # res = StrategyCommon.run_backtest(priceHist['VNM'], MovingAverageStrategy.sma_psar_decision, {'long':15, 'short':7})

# # # bestSma = MovingAverageStrategy.check_best_match_sma(priceHist['VNM'])
# # # import pandas as pd
# # # from Symbol import SymbolHistory
# # # import Indicator

# # # def double_ma_retrace(maLong, maShort, price):
# # #     maDiff = maShort - maLong
# # #     priceDiff = {}
# # #     _diff = {}
# # #     priceDiff[3] = price.diff(3).shift(-3) # On T3, check for different with T0 price
# # #     priceDiff[4] = price.diff().shift(-4) # diff between T3 & T4
# # #     priceDiff[5] = price.diff().shift(-5)
# # #     _diff[3] = priceDiff[3] # If stop at T3, mean T3 is negative, save this negative as result
# # #     _diff[4] = _diff[3] # if stop as T4, save T3 diff as result
# # #     _diff[5] = price.diff(4).shift(-4) # if stop as T5, save T4 as result
# # #     _diff[6] = price.diff(5).shift(-5) # if stop as T6, save T5 as result
# # #     res = {'gold':[], 'death':[]}
# # #     for idx in range(30, len(price)-5):
# # #         if maDiff[idx-1] <= 0 and maDiff[idx] > 0:
# # #             # look ahead to confirm the price
# # #             for p in range(3,6):
# # #                 if priceDiff[p][idx] < 0:
# # #                     res['gold'].append([idx, p-1, _diff[p][idx]])
# # #                     break
# # #             else:
# # #                 # No break, so no negative is found
# # #                 res['gold'].append([idx, 5, _diff[6][idx]])
# # #         if maDiff[idx-1] >= 0 and maDiff[idx] < 0:
# # #             for p in range(3,6):
# # #                 if priceDiff[p][idx] > 0:
# # #                     res['death'].append([idx, p-1, _diff[p][idx]])
# # #                     break
# # #             else:
# # #                 # No break, so no negative is found
# # #                 res['death'].append([idx, 5, _diff[6][idx]])
# # #     return {'gold': pd.DataFrame( 
# # #                  {'diff': [x[2]*3 if x[1]<3 else x[2] for x in res['gold']], # punish for failed signal more by *3
# # #                   't': [x[1] for x in res['gold']],
# # #                   'idx': [x[0] for x in res['gold']]}),
# # #           'death': pd.DataFrame( 
# # #                  {'diff': [x[2]*3 if x[1]<3 else x[2] for x in res['death']],
# # #                   't': [x[1] for x in res['death']],
# # #                   'idx': [x[0] for x in res['death']]} )}
    
# # # def double_ma_list(shortWinLimit=[5,14], maxWin=80):
# # #     res = []
# # #     for sw in range(shortWinLimit[0],shortWinLimit[1]+1):
# # #         for lw in range(min(int(sw*1.5), maxWin), min(int(sw*3), maxWin)+1):
# # #             if [lw,sw] not in res:
# # #                 res.append([lw,sw])
# # #     return res

# # # def triple_ma_list(shortWinLimit=[5,14], maxWin=80):
# # #     res = []
# # #     for sw in range(shortWinLimit[0],shortWinLimit[1]+1):
# # #         for mw in range(min(int(sw*1.5), maxWin), min(int(sw*2.5), maxWin)+1):
# # #             for lw in range(min(int(mw*1.5), maxWin), min(int(mw*2.5), maxWin)+1):
# # #                 if [lw,mw,sw] not in res:
# # #                     res.append([lw,mw,sw])
# # #     return res

# # # def get_best_double_ma(symbol: SymbolHistory, func=None, filter=True):
# # #     print("Finding the best match for Double MA of '%s' ..." % symbol.name, end='', flush=True)
# # #     res = []
# # #     cnt = 20
# # #     price = Indicator.exponential_moving_average(symbol.close,6).shift(-3) # this is better to indicate the trend on some next day
# # #     if func is None: func = symbol.sma
# # #     for lw,sw in double_ma_list():
# # #         maShort = func(sw)
# # #         maLong = func(lw)
# # #         trace = double_ma_retrace(maLong, maShort, price)
# # #         res.append({'win':[lw,sw], 
# # #                 'gold': [trace['gold']['diff'].mean().round(2), trace['gold']['diff'].std().round(2),
# # #                      trace['gold']['t'].mean().round(2), trace['gold']['t'].std().round(2)],
# # #             'death': [trace['death']['diff'].mean().round(2), trace['death']['diff'].std().round(2),
# # #                      trace['death']['t'].mean().round(2), trace['death']['t'].std().round(2)],})
# # #         cnt -= 1
# # #         if cnt == 0:
# # #             print('.', end='', flush=True)
# # #     print(" Done")
    
# # #     if filter:
# # #         best = res[0]
# # #         for r in res:
# # #             if r['gold'][0] >= best['gold'][0] and r['gold'][2] >= 3:
# # #                 ok = True
# # #                 if r['gold'][0] == best['gold'][0]:
# # #                     if r['gold'][1] < best['gold'][1]:
# # #                         ok = False # std of Gold is smaller, dont take it
# # #                     elif r['death'][0] > best['death'][0]:
# # #                         ok = False # negative is smaller
# # #                 if ok:
# # #                     best = r
# # #         return best
# # #     else:
# # #         return res


# def checkIntraSidePower(intra):
#     df = intra.copy()
#     df['_dt'] = pd.to_datetime(df['time'])
#     df = df[(df['_dt'].dt.hour < 14) | (df['_dt'].dt.minute < 30)].reset_index(drop=True) # remove ATC phase
#     df['_m'] = df['mt'].diff()
#     df['_b'] = np.where((df['buy'] == 1) & (df['_m']>0), 1,
#                          0)
#     df['_s'] = np.where((df['buy'] == 0) & (df['_m']>0), 1, 0)
#     offerVol = {}
#     bidVol = {}
#     buyVol = {}
#     sellVol = {}
#     totalVol = {}
#     prices = set()
#     totalX = 0
#     totalN = 0
#     sellN = 0
#     buyN = 0

#     def _addPriceMax(l, p, v):
#         if p == 0: return
#         if p not in l: l[p] = 0
#         if l[p] < v: l[p] = v
#         prices.add(p)


#     for i in range(len(df)):
#         cur = df.loc[i]
#         for i in range(1,4):
#             _addPriceMax(offerVol, cur['op%d'%i], cur['ov%d'%i])
#             _addPriceMax(bidVol, cur['bp%d'%i], cur['bv%d'%i])

#         if cur['_m'] > 0:
#             _t = buyVol if cur['buy'] else sellVol
#             if cur['buy']:
#                 buyN += 1
#             else:
#                 sellN += 1
#             try:
#                 _t[cur['mp']] += cur['mv']
#             except:
#                 _t[cur['mp']] = cur['mv']
#             try:
#                 totalVol[cur['mp']] += cur['mv']
#             except:
#                 totalVol[cur['mp']] = cur['mv']
#             totalX += cur['mv']
#             totalN += 1
#     # print("total %d (%d) buy %d sell %d" % (totalX, totalN, buyN, sellN))
#     prices = sorted(prices)
#     res = pd.DataFrame({
#         'price': prices,
#         'bid': [bidVol[x] if x in bidVol else 0 for x in prices],
#         'buy': [buyVol[x] if x in buyVol else 0 for x in prices],
#         'sell': [sellVol[x] if x in sellVol else 0 for x in prices],
#         'ask': [offerVol[x] if x in offerVol else 0 for x in prices],
#     })

#     # report
#     # for p in sorted(prices):
#     #     print("%0.2f : bid %-06d buy %-06d sell %-06d ask %-06d" % (p,
#     #         bidVol[p] if p in bidVol else 0,
#     #         buyVol[p] if p in buyVol else 0,
#     #         sellVol[p] if p in sellVol else 0,
#     #         offerVol[p] if p in offerVol else 0,
#     #     ))
#     # print("Average: bid %0.2f buy %0.2f sell %0.2f ask %0.2f" % (
#     #     (res['bid'] * res['price']).sum() / res['bid'].sum(),
#     #     (res['buy'] * res['price']).sum() / res['buy'].sum(),
#     #     (res['sell'] * res['price']).sum() / res['sell'].sum(),
#     #     (res['ask'] * res['price']).sum() / res['ask'].sum()
#     # ))
#     # print("TotalVol: bid %-06d buy %-06d sell %-06d ask %-06d" % (
#     #     res['bid'].sum(), res['buy'].sum(), res['sell'].sum(), res['ask'].sum()
#     # ))

#     return res, offerVol, bidVol, buyVol, sellVol, totalVol, prices, totalX

def convertIntra2sql():
    from datetime import datetime
    import re, os, pickle, sqlite3
    import pandas as pd
    import StockAPI

    folderName = 'data/intras_tmp'

    conn = sqlite3.connect('data/intra_test.db')
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS Intra (
            id integer PRIMARY KEY,
            ticket text NOT NULL,
            date integer NOT NULL,
            time integer,
            mp real NOT NULL,
            mv integer NOT NULL,
            mt integer NOT NULL,
            ov1 integer NOT NULL,
            ov2 integer NOT NULL,
            ov3 integer NOT NULL,
            op1 real NOT NULL,
            op2 real NOT NULL,
            op3 real NOT NULL,
            bv1 integer NOT NULL,
            bv2 integer NOT NULL,
            bv3 integer NOT NULL,
            bp1 real NOT NULL,
            bp2 real NOT NULL,
            bp3 real NOT NULL,
            buy integer NOT NULL
            );""")
    
    def insert(items, exe=cursor.executemany):
        exe("""
        INSERT INTO Intra(ticket, date, time, mp, mv, mt,
                          ov1, ov2, ov3, op1, op2, op3,
                          bv1, bv2, bv3, bp1, bp2, bp3, buy)
                    VALUES(?, ?, ?, ?, ?, ?,
                          ?, ?, ?, ?, ?, ?,
                          ?, ?, ?, ?, ?, ?, ?)
        """, items)
    
    def intraGen(ticket, intra, date):
        for i in range(len(intra)):
            x = intra.iloc[i]
            time = int(datetime.strptime('2000 '+x['time'], '%Y %H:%M:%S.%f').timestamp())
            yield [ticket, date, time, x['mp'], x['mv'], x['mt'],
                   x['ov1'], x['ov2'], x['ov3'], x['op1'], x['op2'], x['op3'],
                   x['bv1'], x['bv2'], x['bv3'], x['bp1'], x['bp2'], x['bp3'], int(x['buy'])]

    fnre = re.compile(r'^(...)_(........)\.pkl$')
    fileList = os.listdir(folderName)
    for fname in fileList:
        x = fnre.match(fname)
        if not x:
            continue
        ticket, date = x.groups()
        date = int(datetime.strptime(date + ' 07', '%Y%m%d %H').timestamp())
        intra = pickle.load(open(folderName+'/'+fname, 'rb'))
        print("date", date)

        if intra is None:
            insert([ticket, date, None, 0, 0, 0, # A time=None indicate there's no Data available for this day
                    0,0,0,0,0,0,
                    0,0,0,0,0,0,0], exe=cursor.execute)
        else:
            # intra['date'] = pd.Series(date, index=intra.index)
            # intra['time'] = intra['time'].apply(lambda x: int(datetime.strptime('2000 '+x, '%Y %H:%M:%S.%f').timestamp()))
            insert(intraGen(ticket, intra, date))
    
    conn.commit()
    conn.close()

def getIntra(ticket, date):
    import pandas as pd
    import sqlite3
    conn = sqlite3.connect('data/intra_test.db')
    # conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Intra WHERE ticket = '%s' AND date = %d" % (ticket, date))
    res = cursor.fetchall()
    conn.close()
    if len(res) == 0:
        raise Exception('No entry found for "%s" on %d' % (ticket, date))
    if res[0][3] is None:
        return None
    df = pd.DataFrame(
        columns='date time mp mv mt ov1 ov2 ov3 op1 op2 op3 bv1 bv2 bv3 bp1 bp2 bp3 buy'.split(), 
        index=range(len(res)))
    for i in range(len(res)):
        x = res[i]
        df.at[i, 'date'] = x[2]
        df.at[i, 'time'] = x[3]
        df.at[i, 'mp'] = x[4]
        df.at[i, 'mv'] = x[5]
        df.at[i, 'mt'] = x[6]
        df.at[i, 'ov1'] = x[7]
        df.at[i, 'ov2'] = x[8]
        df.at[i, 'ov3'] = x[9]
        df.at[i, 'op1'] = x[10]
        df.at[i, 'op2'] = x[11]
        df.at[i, 'op3'] = x[12]
        df.at[i, 'bv1'] = x[13]
        df.at[i, 'bv2'] = x[14]
        df.at[i, 'bv3'] = x[15]
        df.at[i, 'bp1'] = x[16]
        df.at[i, 'bp2'] = x[17]
        df.at[i, 'bp3'] = x[18]
        df.at[i, 'buy'] = x[19]
    return df

# conn = sqlite3.connect('data/intra_test.db')
# # conn.row_factory = sqlite3.Row
# cursor = conn.cursor()
# cursor.execute("SELECT * FROM Intra WHERE ticket = 'AAA' AND date = 1614297600")
# res = cursor.fetchall()

def intradayRecheck():
    import re, os, pickle
    from datetime import datetime
    import StockAPI, Symbol

    folderName = 'data/intras'
    folderName2 = 'data/intras_new'
    folderName3 = 'data/intras_fixed'
    fnre = re.compile(r'^(...)_(........)\.pkl$')
    fileList = os.listdir(folderName)
    symbols = {}

    dates = StockAPI.getTradingDate(365*2)
    dateIdx = {}
    for i,v in enumerate(dates):
        dateIdx[v] = i

    srv = StockAPI.IntraServer('vdsc', folderName2)
    errCnt = 0
    fixCnt = 0
    chkCnt = 20

    print('Checking %d ... ' % len(fileList))

    for fname in fileList:
        chkCnt -= 1
        if chkCnt == 0:
            # print('. ', end='', flush=True)
            chkCnt = 20

        x = fnre.match(fname)
        if not x:
            continue
        ticket, dateStr = x.groups()
        date = int(datetime.strptime(dateStr + ' 07', '%Y%m%d %H').timestamp())
        intra = pickle.load(open(folderName+'/'+fname, 'rb'))
        intra2 = srv.intraday(ticket, date)
        if ticket not in symbols:
            symbols[ticket] = Symbol.SymbolHistory(ticket, StockAPI.getPriceHistory(ticket,365*2))

        daily = symbols[ticket].atDate(date)
        if daily is None:
            # print("??? %s %s" % (ticket, dateStr))
            os.remove(folderName+'/'+fname)
            continue

        def totalVol(df):
            dfm = StockAPI.intraMatchedOnly(df)
            return dfm['mv'].sum()

        vol0 = daily.volumn
        vol1 = -1 if intra is None else totalVol(intra)
        volMt1 = -1 if intra is None else intra.iloc[-1]['mt']
        vol2 = -1 if intra2 is None else totalVol(intra2)
        volMt2 = -1 if intra2 is None else intra2.iloc[-1]['mt']

        def volOk(v1, v0):
            if 0.98 < (v1/v0) < 1.02:
                return True
            return False

        if vol0 == 0:
            if vol2 == 0:
                pickle.dump(intra2, open(folderName3+'/'+fname, 'wb'))
            elif vol1 == 0:
                pickle.dump(intra, open(folderName3+'/'+fname, 'wb'))
            else:
                print("Error: [%s] %s: vol1 %d (%d) vol2 %d (%d) vol0 %d" %
                    (ticket, dateStr, vol1, volMt1, vol2, volMt2, vol0))

        elif volOk(vol2, vol0):
            pickle.dump(intra2, open(folderName3+'/'+fname, 'wb'))
        elif volOk(vol1, vol0):
            pickle.dump(intra, open(folderName3+'/'+fname, 'wb'))
        elif volOk(volMt2, vol0):
            intra2['mv'] = intra2['mt'].diff()
            pickle.dump(intra2, open(folderName3+'/'+fname, 'wb'))
        elif volOk(volMt1, vol0):
            intra['mv'] = intra['mt'].diff()
            pickle.dump(intra, open(folderName3+'/'+fname, 'wb'))
        elif vol1 != 0 and vol1 == volMt1 and (vol0/vol1) == 10:
            # VCSC sometime got this wrong in 10 folds...
            intra['mv'] = intra['mv'] * 10
            intra['mt'] = intra['mt'] * 10
            pickle.dump(intra, open(folderName3+'/'+fname, 'wb'))
        else:
            print("Error: [%s] %s: vol1 %d (%d) vol2 %d (%d) vol0 %d" %
                (ticket, dateStr, vol1, volMt1, vol2, volMt2, vol0))
            pickle.dump(None, open(folderName3+'/'+fname, 'wb'))
        

        # if vol0 == 0:
        #     if vol2 == 0:
        #         pickle.dump(intra2, open(folderName3+'/'+fname, 'wb'))
        #     elif vol1 == 0:
        #         pickle.dump(intra, open(folderName3+'/'+fname, 'wb'))
        #     else:
        #         print("Error: [%s] %s: vol1 %d vol2 %d vol0 %d" % (ticket, dateStr, vol1, vol2, vol0))

        # elif vol1 == 0:
        #     if vol2 > 0 and 0.98 < (vol2 / vol0) < 1.02:
        #         pickle.dump(intra2, open(folderName3+'/'+fname, 'wb'))
        #     else:
        #         print("Error: [%s] %s: vol1 %d vol2 %d vol0 %d" % (ticket, dateStr, vol1, vol2, vol0))

        # elif 0.98 < (vol2 / vol0) < 1.02:
        #     pickle.dump(intra2, open(folderName3+'/'+fname, 'wb'))
        # elif 0.98 < (vol1 / vol0) < 1.02:
        #     pickle.dump(intra, open(folderName3+'/'+fname, 'wb'))
        # elif 0.98 < (vol2 / vol1) < 1.02:
        #     if intra is None and intra2 is None:
        #         pickle.dump(intra, open(folderName3+'/'+fname, 'wb'))
        #     else:
        #         print("Info: [%s] %s: recheck this vol1 %d vol2 %d vol0 %d" % (ticket, dateStr, vol1, vol2, vol0))
        # else:
        #     print("Error: [%s] %s: vol1 %d vol2 %d vol0 %d" % (ticket, dateStr, vol1, vol2, vol0))

        # if intra is None:
        #     newIntra = srv.intraday(ticket, date)
        #     continue
        
        

        # def totalVol(df):
        #     dfm = StockAPI.intraMatchedOnly(df)
        #     return dfm['mv'].sum()

        # intraVol = totalVol(intra)
        # dailyVol = daily.volumn
        # if 0.98 < (intraVol / dailyVol) < 1.02:
        #     pass
        # else:
        #     errCnt += 1
        #     # print('ERROR: [%s] %s : %s <> %s' % (ticket, dateStr, intraVol, dailyVol))
        #     # print('Getting %s %s' % (ticket, date))
        #     newIntra = srv.intraday(ticket, date)
        
        

        # if date not in dateIdx:
        #     # print('ERROR: consider remove this file %s' % fname)
        #     os.remove(folderName+'/'+fname)
        #     continue

        # Check the volume
        # if intra is None:
        #     newIntra = srv.intraday(ticket, date, dontsave=True, refetch=True)
        #     pickle.dump(newIntra, open('data/intras_new/'+fname, 'wb'))
        #     continue



        # def totalVol(df):
        #     dfm = StockAPI.intraMatchedOnly(df)
        #     return dfm['mv'].sum()

        # intraVol = totalVol(intra)
        # try:
        #     dailyVol = symbols[ticket].volumn[dateIdx[date]]
        # except Exception as e:
        #     print("??? %s %s %s" % (ticket, dateStr, e))
        # if 0.98 < (intraVol / dailyVol) < 1.02:
        #     pass
        # else:
        #     errCnt += 1
        #     # print('ERROR: [%s] %s : %s <> %s' % (ticket, dateStr, intraVol, dailyVol))
        #     # print('Getting %s %s' % (ticket, date))
        #     newIntra = srv.intraday(ticket, date, dontsave=True, refetch=True)
        #     pickle.dump(newIntra, open('data/intras_new/'+fname, 'wb'))
        #     # if newIntra is not None:
        #     #     newVol = totalVol(newIntra)
        #     #     if 0.98 < (newVol / dailyVol) < 1.02:
        #     #         pickle.dump(newIntra, open('data/intras_new/'+fname, 'wb'))
        #     #         fixCnt += 1
        #     #         continue
        #     # print('ERROR: [%s] %s : %s <> %s' % (ticket, dateStr, intraVol, dailyVol))

    # print('\nTotal error %d' % errCnt)


def polyfit(ps, deg, intv=10):
    import numpy as np
    import pandas as pd
    coeff = []
    resid = [None]*intv
    line = []
    for i in range(deg+1):
        coeff.append([None]*intv)

    for i in range(intv, len(ps)):
        y = ps.iloc[i-intv:i]
        pf, res, _, _, _ = np.polyfit(x=range(intv), y=y, deg=deg, full=True)
        for j in range(deg+1):
            coeff[j].append(pf[j])
        resid.append(res[0])
    # return res
    x = pd.DataFrame({'p%d'%i:v for i,v in enumerate(coeff)})
    x['residuals'] = resid
    return x

# def drawCandleLine(df,line):
#     >>> from plotly.subplots import make_subplots
# >>> fig = make_subplots(rows=2, cols=1)
# >>> fig.add_trace(   

# >>> r = requests.get('https://s.cafef.vn/Ajax/CongTy/BanLanhDao.aspx?sym=VRE')
# >>> from bs4 import BeautifulSoup
# >>> soup = BeautifulSoup(r.text, 'html.parser')

# cd = soup.find('div', {'id':'divViewCoDongLon'})

# >>> klcp = cd.find('table', {'id':'ucBanLanhDao2_tblKLCP'})
# >>> td = klcp.find_all('td')
# >>> len(td)
# 1
# >>> td[0]
# <td align="right" colspan="2" style="border: 1px solid #e2e2e2; padding: 5px 20px 5px 20px; font-weight: bold; color: #343434">
#                                 KL CP đang niêm yết : 2,328,818,410 cp<br/>
#               KL CP đang lưu hành : 2,272,318,410 cp
#                             </td>
# >>> td[0].text
# '\r\n                                KL CP đang niêm yết :\xa02,328,818,410\xa0cp\r\n              KL CP đang lưu hành :\xa02,272,318,410\xa0cp\r\n                            '
# >>> t = td[0].text
# >>> t.strim()
# Traceback (most recent call last):
#   File "<stdin>", line 1, in <module>
# AttributeError: 'str' object has no attribute 'strim'
# >>> t.strip()
# 'KL CP đang niêm yết :\xa02,328,818,410\xa0cp\r\n              KL CP đang lưu hành :\xa02,272,318,410\xa0cp'
# >>> t
# '\r\n                                KL CP đang niêm yết :\xa02,328,818,410\xa0cp\r\n              KL CP đang lưu hành :\xa02,272,318,410\xa0cp\r\n                            '
# >>> t = t.strip()
# >>> t
# 'KL CP đang niêm yết :\xa02,328,818,410\xa0cp\r\n              KL CP đang lưu hành :\xa02,272,318,410\xa0cp'
# >>> t.split('\r\n')
# ['KL CP đang niêm yết :\xa02,328,818,410\xa0cp', '              KL CP đang lưu hành :\xa02,272,318,410\xa0cp']
# >>> t = t.split('\r\n')
# >>> t[0]
# 'KL CP đang niêm yết :\xa02,328,818,410\xa0cp'
# >>> t[0].split('\xa0')
# ['KL CP đang niêm yết :', '2,328,818,410', 'cp']

import pandas as pd

def _combineSymbol(symbols, tickets=None):
    df = {}
    if tickets is None:
        # tickets = [x.name for x in symbols]
        tickets = list(symbols.keys())
    for tic in tickets:
        df[tic] = symbols[tic].close

    df = pd.DataFrame(df)
    sz = len(df)
    for tic in tickets:
        df[tic] = df[tic].shift(sz - symbols[tic].len)
    return df

def equalWeightedIndex(symbols, tickets=None, corrected=False, refval=1000.0):
    if corrected:
        if tickets is None:
            df = symbols
        else:
            df = symbols[tickets]
    else:
        df = _combineSymbol(symbols, tickets)

    isact = ~df.isnull()
    dfsum = df.sum(axis=1)
    adjratio = (df * isact.shift()).sum(axis=1) / dfsum

    ratio = [refval / dfsum.iloc[0]]
    for i in range(1,len(df)):
        ratio.append(ratio[-1] * adjratio.iloc[i])
        
    res = pd.DataFrame({'ratio':ratio, 'adjust':adjratio})
    res['idx'] = dfsum * res.ratio
    # return (res,df)
    return res['idx']

def mktcapWeightedIndex(symbols, tickets, floatShares, refval=1000.0):
    df = _combineSymbol(symbols, tickets)
    for tic in tickets:
        df[tic] = df[tic] * floatShares[tic]

    return equalWeightedIndex(df, corrected=True, refval=refval)

def getAllSymbol(dayNum:int=365*2+50, exchange: str = 'HOSE HNX'):
    import StockAPI, Symbol
    tickets = StockAPI.getAllTickets(exchange)
    print("Getting price history of %d Stocks ..." % len(tickets), end="", flush=True)
    syms = {}
    cnt = 10
    for tic in tickets:
        if len(tic) != 3:
            continue
        symbol = Symbol.SymbolHistory(tic, dayNum=dayNum)
        if symbol.len < 100 or symbol.sma(src='volumn',window=50).iloc[-1]<200000:
            continue
        syms[tic] = symbol
        cnt -= 1
        if cnt == 0:
            print(".", end="", flush=True)
            cnt = 10
    print(" Done")
    return syms

def marketIndexes(symbols, industries, rolling=20):
    close = _combineSymbol(symbols)
    indexes = {}
    sectors = {}
    sectorAbs = {}
    relativeIndexes = {}
    indexes['Whole Market'] = equalWeightedIndex(close, corrected=True)

    def incrPerc(ps):
        return ps.diff(rolling) / ps.shift(rolling)
    mktIncr = incrPerc(indexes['Whole Market'])

    for industry,tickets in industries.items():
        indexes[industry] = equalWeightedIndex(close, tickets=tickets, corrected=True)
        sectorIncr = incrPerc(indexes[industry])
        relativeIndexes[industry] = sectorIncr - mktIncr
        sectorAbs[industry] = {'Index': indexes[industry]}
        sector = {}
        for tic in tickets:
            firstVldId = close[tic].first_valid_index()
            sectorAbs[industry][tic] = close[tic] * (indexes[industry].iloc[firstVldId] / close[tic].iloc[firstVldId])
            sector[tic] = incrPerc(close[tic]) - sectorIncr
        sectors[industry] = pd.DataFrame(sector)
    return {'indexes': pd.DataFrame(indexes), 'relindexes': relativeIndexes, 'sectors': sectors, 'sectorAbs': sectorAbs}

