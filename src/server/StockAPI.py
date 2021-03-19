
import requests, json, datetime, logging

def getAllSymbols(exchanger: str):
    logging.info("Getting All Symbols from Exchanger '%s'" % exchanger)
    r = requests.post("https://gateway-iboard.ssi.com.vn/graphql",
        data={"operationName":None, "variables":{},
              "query": '{%s: stockRealtimes(exchange: "%s") {stockNo stockSymbol exchange __typename }}' % (exchanger, exchanger)})
    if r.status_code != 200:
        logging.error("Failed to get Symbols '%s'" % r.reason)
        return []
    j = json.loads(r.text)
    return [x['stockSymbol'] for x in 
                filter(lambda s: s['__typename'] == 'StockRealtime' and s['exchange'] == exchanger, j['data'][exchanger])]

# def getAllSymbols(exchager: str):
#     logging.info("Getting All Symbols from Exchanger '%s'" % exchanger)
#     r = requests.get("https://iboard.ssi.com.vn/dchart/api/1.1/defaultAllStocks")
#     if r.status_code != 200:
#         logging.error("Failed to get Symbols '%s'" % r.reason)
#         return []
#     j = json.loads(r.content.decode('utf-8'))
#     if j['status'] != 'ok':
#         logging.error('Server return Non-OK response for Stock list')
#         return []
    

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

def getPriceHistory(ticket: str, dayNum: int, tillDate = -1):
    if tillDate == -1: tillDate = datetime.datetime.now()
    fromDate = tillDate - datetime.timedelta(days=dayNum)
    logging.debug('Getting History for "%s" from "%s" - "%s" ...' % (ticket, fromDate.ctime(), tillDate.ctime()))
    j = __getPriceHistory(ticket, fromDate, tillDate)
    if j == None:        return None
    return None if (j==None) else \
        {'high': [float(x) for x in j['h']],
        'low': [float(x) for x in j['l']],
        'open': [float(x) for x in j['o']],
        'close': [float(x) for x in j['c']],
        'volumn': [int(x) for x in j['v']]}

def getTradingDate(dayNum: int, tillDate = -1):
    if tillDate == -1: tillDate = datetime.datetime.now()
    fromDate = tillDate - datetime.timedelta(days=dayNum)
    j = __getPriceHistory('VNM', fromDate, tillDate)
    if j == None: return None
    return j['t']
