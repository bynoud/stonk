

def _combineSymbol(symbols, tickets):
    df = {}
    if tickets is None:
        tickets = [x.name for x in symbols]
    for tic in tickets:
        df[tic] = symbols[tic].close

    df = pd.DataFrame(df)
    sz = len(df)
    for tic in tickets:
        df[tic] = df[tic].shift(sz - symbols[tic].len)
    return df

def equalWeightedIndex(symbols, tickets=None, corrected=False, refval=1000.0):
    if corrected:
        df = symbols
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

