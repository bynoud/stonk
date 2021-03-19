
import pandas as pd
from StockAPI import *

NUM_DAY = 365*2
meta = {}

tickets = getAllSymbols('hose')
meta['tickets'] = tickets
tillDate = datetime.datetime.now()

dates = getTradingDate(NUM_DAY, tillDate)
meta['date'] = dates
tradingSize = len(dates)
df = pd.DataFrame({'date': dates})

hist = {}
for tic in tickets:
    h = getPriceHistory(tic, NUM_DAY, tillDate)
    for val in ["close", "open", "high", "low", "volumn"]:
        df["%s$%s" % (tic, val)] = [None]*(tradingSize-len(hist[tic][val])) + hist[tic][val]
        df["%s$close$percent" % (tic)] = df["%s$close" % tic].pct_change(axis=0, fill_method='bfill')

meta['corr'] = {}
for s1 in range(len(tickets)):
    for s2 in range(s1+1, len(tickets)):
            t1 = tickets[s1]
            t2 = tickets[s2]
            meta['corr']["%s-%s" % (t1,t2)] = df["%s$close$percent" % t1].corr(df["%s$close$percent" % t2])
