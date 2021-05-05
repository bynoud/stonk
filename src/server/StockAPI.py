
import requests, json, datetime, logging, pickle
import pandas as pd
import numpy as np
# from  Symbol import SymbolHistory, simple_moving_average
import StockDB

_OPT = {
    # 'intraServer': 'vcsc',
    'intraServer': 'vdsc',
    'agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
}



class Error(Exception):
    pass

class IntraServer:
    def __init__(self, srv: str, dbDir='data/intras'):
        self.srv = srv
        self._dir = dbDir
        self._retry = 5
        self._cookie = ''
        self.renewCookie()

    def renewCookie(self):
        # print('date', date)
        self._cookie = _getCookie(self.srv)

    def intraday(self, ticket: str, date, dontsave=False, refetch=False):
        if isinstance(date, str):
            dateStr = date
            date = datetime.datetime.strptime(dateStr + ' 07', '%Y%m%d %H') # This is to matched with tradingDate response
        elif isinstance(date, int):
            date = datetime.datetime.fromtimestamp(date)
            dateStr = date.strftime("%Y%m%d")
        else:
            dateStr = date.strftime("%Y%m%d")

        # print('Getting intraday from %s %s %s' % (self.srv, ticket, dateStr))

        fname = '%s/%s_%s.pkl' % (self._dir, ticket, dateStr)
        if not refetch:
            try:
                intra = pickle.load(open(fname, 'rb'))
                return intra
            except:
                pass

        delta = datetime.datetime.now() - date

        ok = False
        while not ok:
            try:
                if self.srv == 'vcsc':
                    intra = intradaySearch_vcsc(ticket, date, self._cookie)
                else:
                    intra = intradaySearch_vdsc(ticket, date, self._cookie)
                ok = True
            except Exception as e:
                self._retry -= 1
                if self._retry <= 0: raise e
                self.renewCookie()
        
        # only save the Intra if this is fetched after 3PM
        # print(now, now.hour)
        if not dontsave and (delta.days > 0 or delta.seconds > 28800):
            pickle.dump(intra, open(fname, 'wb'))
            # StockDB.saveIntra(tic, intra, date, dbCursor)
        return intra

def getAllTickets(exchange: str = 'hose hnx'):
    exchange = exchange.lower().split()
    # logging.info("Getting All Symbols from Exchanger '%s'" % exchanger)
    query = ''
    for e in exchange:
        query += '%s: stockRealtimes(exchange: "%s") {stockNo stockSymbol exchange __typename }' % (e,e)
    r = requests.post("https://gateway-iboard.ssi.com.vn/graphql",
        data={"operationName":None, "variables":{}, "query": '{%s}' % query})
    if r.status_code != 200:
        # logging.error("Failed to get Symbols '%s'" % r.reason)
        print("Error: Failed to get Symbols '%s'" % r.reason)
        return []
    j = json.loads(r.text)
    result = []
    for e in exchange:
        result += [x['stockSymbol'] for x in j['data'][e]]
    return result
    # return [x['stockSymbol'] for x in 
    #             filter(lambda s: s['__typename'] == 'StockRealtime' and s['exchange'] in exchange, j['data'][exchanger])]

# def getAllTickets(exchange: str = "HOSE HNX"):
#     logging.info("Getting All Symbols from Exchange '%s'" % exchange)
#     r = requests.get("https://iboard.ssi.com.vn/dchart/api/1.1/defaultAllStocks")
#     if r.status_code != 200:
#         logging.error("Failed to get Symbols '%s'" % r.reason)
#         return []
#     j = json.loads(r.text)
#     if j['status'] != 'ok':
#         logging.error('Server return Non-OK response for Stock list')
#         return []
#     return list(
#         map(lambda y: y['code'],
#             filter(lambda x: x['exchange'] in exchange and x['type']=='stock', j['data'])))
    
# SSI does not give Adjusted price (ex, after Split or additional stock sell)
# def __getPriceHistory(ticket: str, fromDate: datetime.datetime, tillDate: datetime.datetime):
#     r = requests.get('https://iboard.ssi.com.vn/dchart/api/history?resolution=D&symbol=%s&from=%0d&to=%0d' %
#                         (ticket, fromDate.timestamp(), tillDate.timestamp()))
#     if r.status_code != 200:
#         logging.error('Failed to get history of "%s": "%s"' % (ticket, r.reason))
#         return None
#     else:
#         try:
#             j = json.loads(r.content.decode('utf-8'))
#             if j['s'] != 'ok':
#                 logging.error('Server return Non-OK response for history of "%s"' % ticket)
#                 return None
#             return j
#         except (json.decoder.JSONDecodeError, IndexError) as e:
#             logging.error('Failed to parse the history response for "%s": "%s"' % (ticket, e.msg))

def __getPriceHistory(ticket: str, fromDate: datetime.datetime, tillDate: datetime.datetime):
    r = requests.get('https://dchart-api.vndirect.com.vn/dchart/history?resolution=D&symbol=%s&from=%0d&to=%0d' %
                        (ticket, fromDate.timestamp(), tillDate.timestamp()))
    if r.status_code != 200:
        raise Error('Failed to get history of "%s": "%s"' % (ticket, r.reason))
    else:
        try:
            j = json.loads(r.text)
            if j['s'] != 'ok':
                raise Error('Server return Non-OK response for history of "%s"' % ticket)
            return j
        except (json.decoder.JSONDecodeError, IndexError) as e:
            logging.error('Failed to parse the history response for "%s": "%s"' % (ticket, e.msg))

def getPriceHistory(ticket: str, dayNum: int, tillDate = -1):
    if tillDate == -1: tillDate = datetime.datetime.now()
    fromDate = tillDate - datetime.timedelta(days=dayNum)
    logging.debug('Getting History for "%s" from "%s" - "%s" ...' % (ticket, fromDate.ctime(), tillDate.ctime()))
    j = __getPriceHistory(ticket, fromDate, tillDate)
    return None if (j==None) else {'high': j['h'],
                                    'low': j['l'],
                                    'open': j['o'],
                                    'close': j['c'],
                                    'volumn': j['v'],
                                    'time': j['t']}

# def getPriceHistoryAll(dayNum: int = 365*2+50, exchange:str='HOSE HNX') -> {str:SymbolHistory}:
#     print("Getting price history of all Stocks...", end="", flush=True)
#     tickets = getAllTickets(exchange)
#     price = {}
#     cnt = 5
#     for tic in tickets:
#         symbol = getPriceHistory(tic, dayNum)
#         if symbol.len > 200 and simple_moving_average(symbol.volumn, 7).iloc[-1] > 50000:
#             price[tic] = symbol
#         cnt -= 1
#         if cnt == 0:
#             print(".", end="", flush=True)
#             cnt = 5
#     print(" Done")
#     return price

def getTradingDate(dayNum: int, tillDate = -1):
    if tillDate == -1: tillDate = datetime.datetime.now()
    fromDate = tillDate - datetime.timedelta(days=dayNum)
    j = __getPriceHistory('VNM', fromDate, tillDate)
    if j == None: return None
    return j['t']

# def getIntradayBook(ticket: str):
#     referer = 'https://finance.vietstock.vn/%s/thong-ke-giao-dich.htm' % ticket
#     client = requests.session()
#     client.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'}
#     getRes = client.get(referer)
#     # print("getRes", getRes)
#     from lxml import etree
#     from io import StringIO
#     if getRes.status_code != 200:
#         print("ERROR: Failed at the first get '%s'" % getRes.reason)
#         return
#     parser = etree.HTMLParser()
#     tree = etree.parse(StringIO(getRes.content.decode("utf-8")), parser=parser)
#     forms = tree.xpath('//*[@id="__CHART_AjaxAntiForgeryForm"]')
#     if len(forms) < 1:
#         print("ERROR: failed to find AntiForgeryForm")
#         return
#     tokEle = forms[0].find('input[@name="__RequestVerificationToken"]')
#     if tokEle is None:
#         print("ERROR: failed to find RequestToken")
#     reqToken = tokEle.get('value')
#     # print("Token: ", reqToken)
#     postRes = client.post('https://finance.vietstock.vn/data/getstockdealdetail',
#         headers={'Referer':referer, 'Origin':'https://finance.vietstock.vn'},
#         data={'code':ticket, 'seq':0, '__RequestVerificationToken':reqToken})
#     if postRes.status_code != 200:
#         print("ERROR: Failed to post the request '%s'" % postRes.reason)
#         return
#     return json.loads(postRes.content.decode('utf-8'))

def __getIntradayBooks(tickets, result) -> (bool, str):
    referer = 'https://finance.vietstock.vn/VNM/thong-ke-giao-dich.htm'
    client = requests.session()
    client.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'}
    getRes = client.get(referer)
    # print("getRes", getRes)
    from lxml import etree
    from io import StringIO
    if getRes.status_code != 200:
        # print("ERROR: Failed at the first get '%s'" % getRes.reason)
        return False, 'Failed at the first get "%s"' % getRes.reason
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(getRes.content.decode("utf-8")), parser=parser)
    forms = tree.xpath('//*[@id="__CHART_AjaxAntiForgeryForm"]')
    if len(forms) < 1:
        # print("ERROR: failed to find AntiForgeryForm")
        return False, 'failed to find AntiForgeryForm'
    tokEle = forms[0].find('input[@name="__RequestVerificationToken"]')
    if tokEle is None:
        # print("ERROR: failed to find RequestToken")
        return False, 'failed to find RequestToken'
    reqToken = tokEle.get('value')
    # print("Token: ", reqToken)
    # print("Getting Intraday ...", end='', flush=True)
    cnt = 10
    for tic in tickets:
        postRes = client.post('https://finance.vietstock.vn/data/getstockdealdetail',
            headers={'Referer':referer, 'Origin':'https://finance.vietstock.vn'},
            data={'code':tic, 'seq':0, '__RequestVerificationToken':reqToken})
        if postRes.status_code != 200:
            # print("ERROR: Failed to post the request for %s '%s'" % (tic, postRes.reason))
            return False, 'Failed to post the request for %s "%s"' % (tic, postRes.reason)
        try:
            contentTxt = postRes.content.decode('utf-8')
        except Exception as e:
            # print("Error during decode '%s' : %s" % (e, postRes.content))
            return False, 'Error during decode "%s"' % e
        if contentTxt == '':
            result[tic] = []
        else:
            try:
                result[tic] = json.loads(contentTxt)
            except Exception as e:
                # print("Error during parsing result '%s' : %s" % (e, contentTxt))
                return False, '[%s] during parsing json result "%s"' % (tic, e)
        cnt -= 1
        if cnt == 0:
            print('.', end='', flush=True)
            cnt = 10
    return True, ''

def getIntradayBooks(tickets, retry=5):
    print("Getting Intraday Books ...", end='', flush=True)
    result = {}
    ok = False
    while not ok and retry > 0:
        retry -= 1
        selTickets = list(filter(lambda x: x not in result, tickets))
        ok, reason = __getIntradayBooks(selTickets, result)
        if not ok:
            print("Error: %s" % (reason))
    print(' Done')
    return result

def intraMatchedOnly(df):
    return df[df['mt'] != df['mt'].shift(1)].reset_index()
    
def _intraProcess(df, ceil, floor):
    # Sometime there's some weird information happend before 9AM
    try:
        df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')
    except ValueError:
        df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S.%f')

    df = df[df['time'].dt.hour >= 9]
    df = df.loc[(df['mt']==0).idxmin():].reset_index() # drop pre-ATO phase
    # sel = df[df['mt'] != df['mt'].shift(1)].reset_index()  # only check where total matched is changed
    df1 = df.shift(1)
    for i in range(1,4):
        df.loc[(df['op%d'%i]==0) & (df['ov%d'%i] > 0), ['op%d'%i]] = floor
        df.loc[(df['bp%d'%i]==0) & (df['bv%d'%i] > 0), ['bp%d'%i]] = ceil

    df['buy'] = pd.Series(0, index=df.index)
    df.loc[df['mp'] >= df1['op1'], ['buy']] = 1
    df.loc[(df['mp'] < df1['op1']) & (df['mp'] > df1['bp1']), ['buy']] = -1 # unknow direction

    # at ATO
    # sel = df.iloc[0]
    # df.at[0, 'buy'] = 0 if sel['mp'] >= sel['op1'] else 1 if sel['mp'] <= sel['bp1'] else -1
    # --- Set it to unknow
    df.at[0, 'buy'] = -1

    # at ATC
    # sel = df.iloc[-1]
    # df.at[len(df)-1, 'buy'] = 0 if sel['mp'] >= sel['op1'] else 1 if sel['mp'] <= sel['bp1'] else -1
    df.at[len(df)-1, 'buy'] = -1

    return df

def intradaySearch_vdsc(ticket, date, cookie=''):
    if cookie == '':
        cookie = _getCookie('vdsc')
    if isinstance(date, str):
        dateStr = date
    else:
        dateStr = date.strftime("%d/%m/%Y")
    r = requests.post('https://livedragon.vdsc.com.vn/general/intradaySearch.rv', 
        data={'stockCode':ticket, 'boardDate': dateStr},
        headers={'Cookie':cookie, 'User-Agent': _OPT['agent']}
    )
    if r.status_code != 200:
        raise Error('Failed to get Intra for "%s": %s' % (ticket, r.reason))
    txt = r.content.decode('utf-8')
    if txt == '':
        return None

    try:
        j = json.loads(txt)
    except json.decoder.JSONDecodeError:
        raise Error('Failed to decode Intra for "%s": %s' % (ticket, txt))
    if not j['success']:
        return None # No database found
        # raise Error('Server return failed for Intra "%s" (%s): %s' % (ticket, dateStr, j['message']))

    if len(j['list']) == 0:
        return None # If content is already empty, just save None, so later retry dont need to refetch

    intra = pd.DataFrame(index=range(len(j['list'])),
        columns='mp mv mt time ov1 ov2 ov3 op1 op2 op3 bv1 bv2 bv3 bp1 bp2 bp3'.split())
    ceil, floor = j['list'][0]['CeiPrice'], j['list'][0]['FlrPrice']
    for i,v in enumerate(j['list']):
        intra.at[i] = {
            'time': v['TradeTime'],
            'mp': v['MatchedPrice'], 'mv': v['MatchedVol'], 'mt': v['MatchedTotalVol'],
            'ov1': v['OfferVol1'], 'ov2': v['OfferVol2'], 'ov3': v['OfferVol3'],
            'op1': v['OfferPrice1'], 'op2': v['OfferPrice2'], 'op3': v['OfferPrice3'],
            'bv1': v['BidVol1'], 'bv2': v['BidVol2'], 'bv3': v['BidVol3'],
            'bp1': v['BidPrice1'], 'bp2': v['BidPrice2'], 'bp3': v['BidPrice3'],
        }
    return _intraProcess(intra, ceil, floor)

def _getCookie(srv=None):
    if srv is None:
        srv = _OPT['intraServer']
    # print('date', date)
    if srv == 'vcsc':
        url = 'http://priceboard1.vcsc.com.vn/vcsc/intraday'
    elif srv == 'vdsc':
        url = 'https://livedragon.vdsc.com.vn/general/intradaySearch.rv'
    else:
        raise Error('Wrong Intra Server option: %s' % srv)
    r = requests.get(url, headers={'User-Agent': _OPT['agent']})
    if r.status_code != 200:
        raise Error('Failed to get')
    return r.headers['Set-Cookie']

def intradaySearch_vcsc(tic, date, cookie=''):
    if cookie == '':
        cookie = _getCookie('vcsc')
    dateStr = date.strftime("%Y%m%d")
    # print('Se', tic, date, cookie)
    r = requests.post('http://priceboard1.vcsc.com.vn/vcsc/IntradayDataAjaxService?time=%d' % datetime.datetime.now().timestamp(), 
        data={'data': '{"command":"init","msgid":1,"data":["%s","%s"]}' % (tic, dateStr)},
        headers={'Cookie':cookie, 
            'Host':'priceboard1.vcsc.com.vn', 
            'Origin':'http://priceboard1.vcsc.com.vn',
            'Referer':'http://priceboard1.vcsc.com.vn/vcsc/intraday',
            'User-Agent': _OPT['agent']}
    )
    if r.status_code != 200:
        raise Error('Failed to get Intra for "%s": %s' % (tic, r.reason))
    txt = r.content.decode('utf-8')
    if txt == '':
        return None

    try:
        j = json.loads(txt)
    except json.decoder.JSONDecodeError:
        raise Error('Failed to decode Intra for "%s": %s' % (tic, txt))

    if len(j['content']) == 0:
        return None # If content is already empty, just save None, so later retry dont need to refetch
    
    intra = pd.DataFrame(index=range(len(j['content'])),
        columns='mp mv mt time ov1 ov2 ov3 op1 op2 op3 bv1 bv2 bv3 bp1 bp2 bp3'.split())
    def v2i(s):
        return int(s.replace(',','')) * 10
    def p2f(s):
        return 0.0 if (s in ['ATC', 'ATO']) else float(s)
    ceil, floor = p2f(j['content'][0]['cei']), p2f(j['content'][0]['flo'])
    for i,v in enumerate(j['content']):
        intra.at[i] = {
            'time': v['time'],
            'mp': p2f(v['mat']), 'mv': v2i(v['mvo']), 'mt': v2i(v['tmv']),
            'ov1': v2i(v['sv1']), 'ov2': v2i(v['sv2']), 'ov3': v2i(v['sv3']),
            'op1': p2f(v['sp1']), 'op2': p2f(v['sp2']), 'op3': p2f(v['sp3']),
            'bv1': v2i(v['bv1']), 'bv2': v2i(v['bv2']), 'bv3': v2i(v['bv3']),
            'bp1': p2f(v['bp1']), 'bp2': p2f(v['bp2']), 'bp3': p2f(v['bp3']),
        }
    return _intraProcess(intra, ceil, floor)

def intradaySearch_old(tic, date, cookie='', dbCursor=None):
    date = datetime.datetime.fromtimestamp(date)
    dateStr = date.strftime("%Y%m%d")
    fname = 'data/intras/%s_%s.pkl' % (tic, dateStr)
    # date = datetime.strptime(dateStr + ' 07', '%Y%m%d %H').timestamp() # This is to matched with tradingDate response
    try:
        intra = pickle.load(open(fname, 'rb'))
        # intra = StockDB.getIntra(tic, date, dbCursor)
        return intra
    except:
        pass

    delta = datetime.datetime.now() - date

    if cookie == '':
        cookie = _getCookie()
    if _OPT['intraServer'] == 'vcsc':
        intra = intradaySearch_vcsc(tic, date, cookie)
    else:
        intra = intradaySearch_vdsc(tic, date, cookie)
    
    # only save the Intra if this is fetched after 3PM
    # print(now, now.hour)
    if delta.days > 0 or delta.seconds > 28800:
        pickle.dump(intra, open(fname, 'wb'))
        # StockDB.saveIntra(tic, intra, date, dbCursor)
    return intra


# _SRV = {
#     'vcsc': IntraServer('vcsc'),
#     'vdsc': IntraServer('vdsc'),
# }

def intradaySearch(sym, svrs, idx=-1):
    tic = sym.name
    date = datetime.datetime.fromtimestamp(sym.time.iloc[idx])
    dateStr = date.strftime("%Y%m%d")
    fname = 'data/intras/%s_%s.pkl' % (tic, dateStr)
    # date = datetime.strptime(dateStr + ' 07', '%Y%m%d %H').timestamp() # This is to matched with tradingDate response
    try:
        intra = pickle.load(open(fname, 'rb'))
        # intra = StockDB.getIntra(tic, date, dbCursor)
        return intra
    except:
        pass

    delta = datetime.datetime.now() - date
    dayPassed = delta.days > 0 or delta.seconds > 28800

    dailyVol = sym.volumn.iloc[idx]
    
    def volOk(v1, v0):
        if 0.98 < (v1/v0) < 1.02:
            return True
        return False
    def intraOk(intra):
        if intra is None:
            return False
        vol = intraMatchedOnly(intra)['mv'].sum()
        if volOk(vol, dailyVol):
            return True
        else:
            volMt = intra['mt'].iloc[-1]
            if volOk(volMt, dailyVol):
                intra['mv'] = intra['mt'].diff()
                return True
        return False

    intra1 = svrs['vdsc'].intraday(tic, date, dontsave=True, refetch=True)
    if dayPassed and not intraOk(intra1):
        intra1 = svrs['vcsc'].intraday(tic, date, dontsave=True, refetch=True)
        if not intraOk(intra1):
            vol = intraMatchedOnly(intra1)['mv'].sum()
            volMt = intra1['mt'].iloc[-1]
            if vol == volMt and (dailyVol/vol) == 10:
                # VCSC sometime got this wrong in 10 folds...
                intra1['mv'] = intra1['mv'] * 10
                intra1['mt'] = intra1['mt'] * 10
            else:
                print("Invalid intra. discard it")
                intra1 = None
    
    # only save the Intra if this is fetched after 3PM
    # print(now, now.hour)
    if dayPassed:
        pickle.dump(intra1, open(fname, 'wb'))
        # StockDB.saveIntra(tic, intra, date, dbCursor)
    return intra1


def intradaySearch_worked_full(tic, date, cookie='', dbCursor=None):
    date = datetime.datetime.fromtimestamp(date)
    dateStr = date.strftime("%Y%m%d")
    fname = 'data/intras/%s_%s.pkl' % (tic, dateStr)
    # date = datetime.strptime(dateStr + ' 07', '%Y%m%d %H').timestamp() # This is to matched with tradingDate response
    try:
        intra = pickle.load(open(fname, 'rb'))
        # intra = StockDB.getIntra(tic, date, dbCursor)
        return intra
    except:
        pass

    delta = datetime.datetime.now() - date

    if cookie == '':
        cookie = _getCookie()
    # print('Se', tic, date, cookie)
    r = requests.post('http://priceboard1.vcsc.com.vn/vcsc/IntradayDataAjaxService?time=%d' % datetime.datetime.now().timestamp(), 
        data={'data': '{"command":"init","msgid":1,"data":["%s","%s"]}' % (tic, dateStr)},
        headers={'Cookie':cookie, 
            'Host':'priceboard1.vcsc.com.vn', 
            'Origin':'http://priceboard1.vcsc.com.vn',
            'Referer':'http://priceboard1.vcsc.com.vn/vcsc/intraday'}
    )
    if r.status_code != 200:
        raise Error('Failed to get Intra for "%s": %s' % (tic, r.reason))
    txt = r.content.decode('utf-8')
    if txt == '':
        # print('It empty return')
        return None

    try:
        j = json.loads(txt)
    except json.decoder.JSONDecodeError:
        raise Error('Failed to decode Intra for "%s": %s' % (tic, txt))

    if len(j['content']) == 0:
        # print("It empty content '%s'" % j)
        intra = None # If content is already empty, just save None, so later retry dont need to refetch
    
    else:
        intra = pd.DataFrame(index=range(len(j['content'])),
            columns='mp mv mt time ov1 ov2 ov3 op1 op2 op3 bv1 bv2 bv3 bp1 bp2 bp3'.split())
        def v2i(s):
            return int(s.replace(',','')) * 10
        def p2f(s):
            return 0.0 if (s in ['ATC', 'ATO']) else float(s)
        ceil, floor = p2f(j['content'][0]['cei']), p2f(j['content'][0]['flo'])
        for i,v in enumerate(j['content']):
            intra.at[i] = {
                'time': v['time'],
                'mp': p2f(v['mat']), 'mv': v2i(v['mvo']), 'mt': v2i(v['tmv']),
                'ov1': v2i(v['sv1']), 'ov2': v2i(v['sv2']), 'ov3': v2i(v['sv3']),
                'op1': p2f(v['sp1']), 'op2': p2f(v['sp2']), 'op3': p2f(v['sp3']),
                'bv1': v2i(v['bv1']), 'bv2': v2i(v['bv2']), 'bv3': v2i(v['bv3']),
                'bp1': p2f(v['bp1']), 'bp2': p2f(v['bp2']), 'bp3': p2f(v['bp3']),
            }
        intra = _intraProcess(intra, ceil, floor)

    # only save the Intra if this is fetched after 3PM
    # print(now, now.hour)
    if delta.days > 0 or delta.seconds > 28800:
        pickle.dump(intra, open(fname, 'wb'))
        # StockDB.saveIntra(tic, intra, date, dbCursor)
    return intra

def fetchIntradayAllSymbols(symbols):
    print('Getting Intra for %d symbols ...' % (len(symbols)), end='', flush=True)
    # print('date', date)
    res = {}
    svrs = {
        'vcsc': IntraServer('vcsc'),
        'vdsc': IntraServer('vdsc'),
    }

    # cursor = StockDB.getCursor()
    cnt = 10
    for sym in symbols:
        # res[tic] = intradaySearch(tic, date, cookie, cursor)
        res[sym.name] = intradaySearch(sym, svrs)
        cnt -= 1
        if cnt <= 0:
            print('.', end='', flush=True)
            cnt = 10
    print('Done')
    # StockDB.close(cursor)
    # return res

def getIntradayHistory(symbol, lookback=20, matchedOnly=False):
    if lookback > symbol.len:
        lookback = symbol.len
    res = []
    print('Getting Intra History of "%s" in %d days ...' % (symbol.name, lookback), end='', flush=True)
    cnt = 10
    # cursor = StockDB.getCursor()
    svrs = {
        'vcsc': IntraServer('vcsc'),
        'vdsc': IntraServer('vdsc'),
    }

    # while retry > 0:
    failed = 0
    for i in range(lookback):
        # dateStr = datetime.datetime.fromtimestamp(dates[i]).strftime("%Y%m%d")
        # intra = intradaySearch(ticket, dates[i], cookie, cursor)
        intra = intradaySearch(symbol, svrs, -i-1)
        if intra is None:
            failed += 1
            if failed > 5: # result for some day may not avaiable?!?
                break # no more result available
        else:
            failed = 0
            if matchedOnly:
                intra = intraMatchedOnly(intra)
        res.insert(0, intra)
        cnt -= 1
        if cnt <= 0:
            print('.',end='',flush=True)
            cnt = 10
    for i in range(lookback-len(res)):
        res.insert(0, None)
    print('Done')
    # StockDB.close(cursor)
    return res


# def getIntradayBookAll(exchange:str='HOSE HNX'):
#     print("Getting price history of all Stocks in '%s'..." % exchange, end="", flush=True)
#     tickets = getAllTickets(exchange)
#     price = {}
#     cnt = 5
#     for tic in tickets:
#         price[tic] = getIntradayBook(tic)
#         cnt -= 1
#         if cnt == 0:
#             print(".", end="", flush=True)
#             cnt = 5
#     print(" Done")
#     return price