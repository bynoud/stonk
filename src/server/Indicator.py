
import pandas as pd

def simple_moving_average(ps: pd.Series, window:int):
    return ps.rolling(window=window, min_periods=window).mean()

def exponential_moving_average(ps: pd.Series, window:int):
    return ps.ewm(span=window, min_periods=window, adjust=False).mean() # a = 2/(1+window)

# Is this also Relative Moving Average (RMA) of TradingView? seem like so, but there's some drift around...
def modified_moving_average(ps: pd.Series, window:int):
    return ps.ewm(com=window-1, min_periods=window, adjust=False).mean() # a = 1/(1+com) = 1/window

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
    rolDown = modified_moving_average(dDown, window)
    rs = rolUp / rolDown
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

INDICATORS = {
    'sma': simple_moving_average,
    'ema': exponential_moving_average,
    'macd': ma_convergence_divergence,
    'rsi': relative_strength_index,
    'ao': awesome_oscillator,
    'bb': bollinger_band,
    'atr': average_true_range,
}

