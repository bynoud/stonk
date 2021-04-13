
import pandas as pd

def simple_moving_average(ps: pd.Series, window:int):
    return ps.rolling(window=window, min_periods=window).mean()

def exponential_moving_average(ps: pd.Series, window:int):
    return ps.ewm(span=window, min_periods=window, adjust=False).mean() # a = 2/(1+window)

# Is this also Relative Moving Average (RMA) of TradingView? seem like so, but there's some drift around...
# seem to be also "Wilders Smoothing"
def modified_moving_average(ps: pd.Series, window:int):
    return ps.ewm(com=window-1, min_periods=window, adjust=False).mean() # a = 1/(1+com) = 1/window

def volumn_weighted_moving_average(price: pd.Series, volumn: pd.Series, window: int):
    pv = price * volumn
    return pv.rolling(window=window).sum() / volumn.rolling(window=window).sum()

def ma_convergence_divergence(ps: pd.Series, shortWin=12, longWin=26, smooth=9):
    macd = exponential_moving_average(ps, shortWin) - exponential_moving_average(ps, longWin)
    signal = exponential_moving_average(macd, smooth)
    hist = macd - signal
    return {'macd':macd, 'signal':signal, 'hist': hist}

# We using a = 1/N (Wilder’s Smoothing Method)
def relative_strength_index(ps: pd.Series, window: int = 14):
    delta = ps.diff()
    dUp, dDown = delta.copy(), delta.copy()
    dUp[dUp < 0] = 0
    dDown[dDown > 0] = 0
    rolUp = modified_moving_average(dUp, window)
    rolDown = modified_moving_average(dDown.abs(), window)
    rs = rolUp / rolDown
    print(rs.tail(10))
    rsi = 100.0 - 100.0 / (1.0 + rs)
    return rsi

# awesome_oscillator
def awesome_oscillator(hig: pd.Series, low: pd.Series, shortWin:int=5, longWin:int=34):
    mid = (hig + low) / 2
    return simple_moving_average(mid, shortWin) - simple_moving_average(mid, longWin)

def bollinger_band(ps: pd.Series, window=20, stddev=2.0):
    sma = ps.rolling(window=window).mean()
    rstd = ps.rolling(window=window).std()
    upper = sma + stddev * rstd
    lower = sma - stddev * rstd
    return {'sma': sma, 'upper': upper, 'lower': lower}

def average_true_range(high:pd.Series, low:pd.Series, window=14):
    tr = high - low
    atr = modified_moving_average(tr, window)
    return atr

def parabolic_sar(high:pd.Series, low:pd.Series, increment:float=0.02, init_af:float=0.02, max_af:float=0.2):
    # ep : current Extreme Point, af: Acceleration Factor
    af = init_af
    sar = pd.Series().reindex_like(high)
    bullS = pd.Series().reindex_like(high)

    # First SAR just simply check for 2 first high point, and assume market in that direction
    if high.iloc[0] < high.iloc[1]:
        bullish, psar, ep = True, min(low.iloc[0], low.iloc[1]), max(high.iloc[0], high.iloc[1])
    else:
        bullish, psar, ep = False, max(high.iloc[0], high.iloc[1]), min(low.iloc[0], low.iloc[1])
    
    # IMPORTANCE!!! sar(n) is actually the sar for next day (since we don't want to increase the size of return array)
    sar[0] = psar
    bullS[0] = bullish
    for idx in range(1, len(high)):
        # Check if trend is reverse
        if (bullish and psar >= low[idx]) or (not bullish and psar <= high[idx]):
            bullish = not bullish
            psar, ep, af = ep, high[idx] if bullish else low[idx], init_af
        else:
            nep = max(ep, high[idx]) if bullish else min(ep, low[idx])   # EP for today
            if af < max_af and nep != ep: af += increment
            ep = nep

        nsar = psar + af * (ep - psar)
        if bullish: nsar = min(nsar, low[idx], low[idx-1])
        else:       nsar = max(nsar, high[idx], high[idx-1])
        psar = nsar
        sar[idx] = nsar
        bullS[idx] = bullish

    return pd.DataFrame({'sar':sar, 'bullish':bullS})

def super_trend(high: pd.Series, low: pd.Series, close: pd.Series, factor:int=3, window:int=7):
    atrFactor = average_true_range(high, low, window) * factor
    hl2 = (high + low) / 2.0
    Up=hl2-atrFactor
    Dn=hl2+atrFactor

    TrendUp = Up.copy()
    TrendDown = Dn.copy()
    Trend = pd.Series(True, range(len(high)))
    Tsl = Up.copy()
    for idx in range(1, len(high)):
        TrendUp[idx] = max(Up[idx],TrendUp[idx-1]) if (close[idx-1]>TrendUp[idx-1]) else Up[idx]
        TrendDown[idx] = min(Dn[idx],TrendDown[idx-1]) if (close[idx-1]<TrendDown[idx-1]) else Dn[idx]

        Trend[idx] = True if (close[idx] > TrendDown[idx-1]) else \
                     False if (close[idx] < TrendUp[idx-1]) else Trend[idx-1]
        Tsl[idx] = TrendUp[idx] if Trend[idx] else TrendDown[idx]
    return {'st':Tsl, 'bull': Trend}

def adx(high: pd.Series, low: pd.Series, smooth:int=14, di_len:int=14):
    diffHigh, diffLow = high.diff(), low.diff()
    diffHighAbs, diffLowAbs = diffHigh.abs(), diffLow.abs()
    posDM, negDM = diffHigh.abs(), diffLow.abs()
    posDM[ (diffHighAbs <= diffLowAbs) | (diffHigh < 0) ] = 0.0
    negDM[ (diffLowAbs <= diffHighAbs) | (diffLow < 0) ] = 0.0
    atr = average_true_range(high, low, di_len)
    posDI = modified_moving_average(posDM, smooth) * 100.0 / atr
    negDI = modified_moving_average(negDM, smooth) * 100.0 / atr
    dx = (posDI - negDI).abs() * 100.0 / (posDI + negDI)
    adx = modified_moving_average(dx, smooth)
    return {'adx': adx, 'pos': posDI, 'neg': negDI}

INDICATORS = {
    'sma': simple_moving_average,
    'ema': exponential_moving_average,
    'macd': ma_convergence_divergence,
    'rsi': relative_strength_index,
    'ao': awesome_oscillator,
    'bb': bollinger_band,
    'atr': average_true_range,
}

