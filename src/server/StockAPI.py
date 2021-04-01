
import requests, json, datetime, logging
import pandas as pd
from  Symbol import SymbolHistory, simple_moving_average

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
    

def __getPriceHistory(ticket: str, fromDate: datetime.datetime, tillDate: datetime.datetime):
    r = requests.get('https://iboard.ssi.com.vn/dchart/api/history?resolution=D&symbol=%s&from=%0d&to=%0d' %
                        (ticket, fromDate.timestamp(), tillDate.timestamp()))
    if r.status_code != 200:
        logging.error('Failed to get history of "%s": "%s"' % (ticket, r.reason))
        return None
    else:
        try:
            j = json.loads(r.content.decode('utf-8'))
            if j['s'] != 'ok':
                logging.error('Server return Non-OK response for history of "%s"' % ticket)
                return None
            return j
        except (json.decoder.JSONDecodeError, IndexError) as e:
            logging.error('Failed to parse the history response for "%s": "%s"' % (ticket, e.msg))

def getPriceHistory(ticket: str, dayNum: int, tillDate = -1) -> SymbolHistory:
    if tillDate == -1: tillDate = datetime.datetime.now()
    fromDate = tillDate - datetime.timedelta(days=dayNum)
    logging.debug('Getting History for "%s" from "%s" - "%s" ...' % (ticket, fromDate.ctime(), tillDate.ctime()))
    j = __getPriceHistory(ticket, fromDate, tillDate)
    return None if (j==None) else {'high': [float(x) for x in j['h']],
                                    'low': [float(x) for x in j['l']],
                                    'open': [float(x) for x in j['o']],
                                    'close': [float(x) for x in j['c']],
                                    'volumn': [int(x) for x in j['v']],
                                    'time': [int(x) for x in j['t']]}

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