import pandas as pd
import pickle
import StockAPI


def getAllIndexes(refetch=False):
    if refetch:
        dates = StockAPI.getTradingDate(200)
        # FIXME# tickets = list(filter(lambda x: len(x)==3, StockAPI.getAllTickets()))
        tickets = pickle.load(open('data/appdb/selTics.pkl','rb'))
        prices = pd.DataFrame(index=dates, columns=tickets)
        print(len(prices), len(tickets))
        selTics = []
        # sharesOuts = {}
        print("Getting %0d tickets prices..." % len(tickets))
        for tic in tickets:
            p = pd.DataFrame(StockAPI.getPriceHistory(tic,200))
            pickle.dump(p, open('data/appdb/tmp/%s.pkl'%tic,'wb'))
            prices.loc[p.time, tic] = p.close
            if (len(p) > 50 and 
                p.volumn.rolling(window=50).mean().iloc[-1] > 200000 and
                p.close.iloc[-1] >= 5):
                selTics.append(tic)
                # sharesOuts[tic] = StockAPI.getSharesOutstanding(tic)
        industries = StockAPI.getIndustries(selTics)
        pickle.dump(selTics, open('data/appdb/selTics.pkl','wb'))
        pickle.dump(industries, open('data/appdb/industries.pkl','wb'))
        pickle.dump(prices, open('data/appdb/prices.pkl','wb'))
        # pickle.dump(sharesOuts, open('data/appdb/sharesOuts.pkl','wb'))
        sharesOuts = pickle.load(open('data/appdb/sharesOuts.pkl','rb'))
    else:
        selTics = pickle.load(open('data/appdb/selTics.pkl','rb'))
        industries = pickle.load(open('data/appdb/industries.pkl','rb'))
        prices = pickle.load(open('data/appdb/prices.pkl','rb'))
        sharesOuts = pickle.load(open('data/appdb/sharesOuts.pkl','rb'))

    mktcap = {}          
    for tic in selTics:
        mktcap[tic] = prices[tic] * sharesOuts[tic]
    mktcap = pd.DataFrame(mktcap, index=prices.index)
    indexes = {}
    for idx, tics in industries.items():
        indexes[idx] = equalWeightedIndex(mktcap, tics)
    
    indexes['all'] = equalWeightedIndex(mktcap, selTics)
    return indexes

def rrg(indexes, benmark, adjusted=False):
    ind = list(indexes.keys())
    rs = {}
    mom = {}
    for i in ind:
        rel = indexes[i] / benmark
        if not adjusted:
            rel = rel * (1.0 / rel.iloc[0])
        roll = rel.rolling(window=50)
        rs[i] = (rel - roll.mean()) / roll.std()
        diff = rs[i].diff(10)
        roll = diff.rolling(window=50)
        mom[i] = (diff - roll.mean()) / roll.std()

        rs[i] = rs[i].rolling(window=10).mean()
        mom[i] = mom[i].rolling(window=10).mean()
    
    import plotly.graph_objects as go
    fig = go.Figure()
    for i in ind:
        fig.add_trace(go.Line(x=rs[i].iloc[-15:], y=mom[i].iloc[-15:], name=i, hovertext=i))
        fig.add_trace(go.Scatter(x=rs[i].iloc[-1:], y=mom[i].iloc[-1:], marker=dict(size=10)))
    return {'rs':rs, 'mom':mom, 'fig':fig}

# def _combineSymbol(symbols, tickets):
#     df = {}
#     if tickets is None:
#         tickets = [x.name for x in symbols]
#     for tic in tickets:
#         df[tic] = symbols[tic].close

#     df = pd.DataFrame(df)
#     sz = len(df)
#     for tic in tickets:
#         df[tic] = df[tic].shift(sz - symbols[tic].len)
#     return df

def equalWeightedIndex(df, tickets=None, refval=1000.0):
    # if corrected:
    #     df = symbols
    # else:
    #     df = _combineSymbol(symbols, tickets)
    if tickets is not None:
        df = df[tickets]

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

def mktcapWeightedIndex(df, tickets, floatShares, refval=1000.0):
    df = df[tickets]
    for tic in tickets:
        df.loc[tic] = df[tic] * floatShares[tic]

    return equalWeightedIndex(df, refval=refval)

