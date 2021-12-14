
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import StockAPI

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


class SymbolHistory:

    def __init__(self, name:str, price=None, dayNum=200):
        if price is None:
            price = StockAPI.getPriceHistory(name, dayNum)
        self._name = name
        self._df = pd.DataFrame(price)
        self._dateIdx = {v:i for i,v in enumerate(price['time'])}
        self._len = len(price['close'])

    @property
    def name(self): return self._name
    @property
    def len(self): return self._len
    @property
    def open(self): return self._df['open']
    @property
    def close(self): return self._df['close']
    @property
    def high(self): return self._df['high']
    @property
    def low(self): return self._df['low']
    @property
    def volumn(self): return self._df['volumn']
    @property
    def time(self): return self._df['time']

    @property
    def ohcl(self): return self._df[['open','high','close','low']]

    def atDate(self, date):
        try:
            return self._df.iloc[self._dateIdx[date]]
        except (IndexError, KeyError):
            # print('something wrong atDate %s %s' % (self.name, date))
            # exit()
            return None

    def sma(self, window:int, src:str='close'): 
        return simple_moving_average(self._df[src], window)
    def ema(self, window:int, src:str='close'): 
        return exponential_moving_average(self._df[src], window)
    def mma(self, window:int, src:str='close'): 
        return modified_moving_average(self._df[src], window)
    def vwma(self, window: int, src:str='close'): 
        return volumn_weighted_moving_average(self._df[src], self.volumn, window)

    # Average True Range
    def atr(self, window:int=14):
        tdf = pd.DataFrame()
        tdf['h-l'] = self.high - self.low
        tdf['h-c'] = (self.high - self.close.shift(1)).abs()
        tdf['l-c'] = (self.low - self.close.shift(1)).abs()
        tdf['tr'] = tdf[['h-l', 'h-c', 'l-c']].max(axis=1)
        return modified_moving_average(tdf['tr'], window)

    # Average directional movement    
    def adx(self, smooth:int=14, di_len:int=14):
        df = pd.DataFrame()
        df['H-pH'] = self.high.diff()
        df['pL-L'] = -self.low.diff()
        df['+DX'] = np.where(
            (df['H-pH'] > df['pL-L']) & (df['H-pH']>0),
            df['H-pH'],
            0.0
        )
        df['-DX'] = np.where(
            (df['H-pH'] < df['pL-L']) & (df['pL-L']>0),
            df['pL-L'],
            0.0
        )
        df['S+DM'] = modified_moving_average(df['+DX'], di_len)
        df['S-DM'] = modified_moving_average(df['-DX'], di_len)
        df['+DI'] = (df['S+DM']/self.atr(di_len))*100
        df['-DI'] = (df['S-DM']/self.atr(di_len))*100
        df['adx'] = modified_moving_average(
            ((df['+DI'] - df['-DI']).abs() / (df['+DI'] + df['-DI']))*100,
            smooth
        )
        return df[['adx', '+DI', '-DI']]

    def rsi(self, window: int = 14, src='close'):
        ps = self._df[src]
        delta = ps.diff()
        dUp, dDown = delta.copy(), delta.copy()
        dUp[dUp < 0] = 0
        dDown[dDown > 0] = 0
        rolUp = modified_moving_average(dUp, window)
        rolDown = modified_moving_average(dDown.abs(), window)
        rs = rolUp / rolDown
        return ( 100.0 - 100.0 / (1.0 + rs))

    # parabolic_sar
    def parabolic_sar(self, increment:float=0.02, init_af:float=0.02, max_af:float=0.2):
        
        # ep : current Extreme Point, af: Acceleration Factor
        af = init_af
        sar = pd.Series(0.0, range(self._len))
        bullS = pd.Series(True, range(self._len))

        # First SAR just simply check for 2 first high point, and assume market in that direction
        if self.high.iloc[0] < self.high.iloc[1]:
            bullish, psar, ep = True, min(self.low.iloc[0], self.low.iloc[1]), max(self.high.iloc[0], self.high.iloc[1])
        else:
            bullish, psar, ep = False, max(self.high.iloc[0], self.high.iloc[1]), min(self.low.iloc[0], self.low.iloc[1])
        
        # IMPORTANCE!!! sar(n) is actually the sar for next day (since we don't want to increase the size of return array)
        sar[0] = psar
        bullS[0] = bullish
        for idx in range(1, self._len):
            # Check if trend is reverse
            if (bullish and psar >= self.low[idx]) or (not bullish and psar <= self.high[idx]):
                bullish = not bullish
                psar, ep, af = ep, self.high[idx] if bullish else self.low[idx], init_af
            else:
                nep = max(ep, self.high[idx]) if bullish else min(ep, self.low[idx])   # EP for today
                if af < max_af and nep != ep: af += increment
                ep = nep

            nsar = psar + af * (ep - psar)
            if bullish: nsar = min(nsar, self.low[idx], self.low[idx-1])
            else:       nsar = max(nsar, self.high[idx], self.high[idx-1])
            psar = nsar
            sar[idx] = nsar
            bullS[idx] = bullish

        return pd.DataFrame({'sar': sar, 'trend': bullS})

    def testPlot(self):
        fig = go.Figure()
        x = pd.Series(range(self._len))

        # Add traces
        fig.add_trace(go.Scatter(x=x, y=self.parabolic_sar(),
                            mode='markers',
                            name='SAR'))
        fig.add_trace(go.Scatter(x=x, y=self.close,
                            mode='lines+markers',
                            name='Close'))
        fig.show()

    # bollinger_band
    def bb(self, window=20, stddev=2.0):
        sma = self.close.rolling(window=window).mean()
        rstd = self.close.rolling(window=window).std()
        upper = sma + stddev * rstd
        lower = sma - stddev * rstd
        return pd.DataFrame({'sma': sma, 'upper':upper, 'lower': lower})

    # Super trend
    def super_trend(self, factor:int=3, window:int=7):
        atrFactor = self.atr(window) * factor
        hl2 = (self.high + self.low) / 2.0
        Up=hl2-atrFactor
        Dn=hl2+atrFactor

        TrendUp = Up.copy()
        TrendDown = Dn.copy()
        Trend = pd.Series(True, range(self.len))
        Tsl = Up.copy()
        for idx in range(1, self.len):
            TrendUp[idx] = max(Up[idx],TrendUp[idx-1]) if (self.close[idx-1]>TrendUp[idx-1]) else Up[idx]
            TrendDown[idx] = min(Dn[idx],TrendDown[idx-1]) if (self.close[idx-1]<TrendDown[idx-1]) else Dn[idx]

            Trend[idx] = True if (self.close[idx] > TrendDown[idx-1]) else \
                        False if (self.close[idx] < TrendUp[idx-1]) else Trend[idx-1]
            Tsl[idx] = TrendUp[idx] if Trend[idx] else TrendDown[idx]
        return {'st':Tsl, 'bull': Trend}

    # Heikin Ashi
    def heikin_ashi(self):
        ha = pd.DataFrame({
            '_h': self.high, '_l': self.low,
            'close': (self.open + self.high + self.low + self.close) / 4,
            'open': pd.Series(range(self.len), dtype=float)
        })
        ha['open'].at[0] = (self.open[0] + self.close[0]) / 2.0
        for i in range(1, self.len):
            ha['open'].at[i] = (ha['open'][i-1] + ha['close'][i-1]) / 2.0
        ha['high'] = ha[['_h', 'open', 'close']].max(axis=1)
        ha['low'] = ha[['_l', 'open', 'close']].min(axis=1)
        return ha[['open', 'close', 'high', 'low']]

class SymbolIntra:
    def __init__(self, name:str, intra):
        self._intra = intra
        if intra is not None:
            self._matched = intra[intra['mt'] != intra['mt'].shift(1)].reset_index()
            self._buy = self._matched[self._matched['buy']==1]
            self._sell = self._matched[self._matched['buy']==0]

    @property
    def buy(self):
        return self._buy
    @property
    def sell(self):
        return self._sell
    @property
    def buyVol(self):
        return 1 if self._intra is None else self._buy['mv'].sum()
    @property
    def sellVol(self):
        return 1 if self._intra is None else self._sell['mv'].sum()
    @property
    def buyVal(self):
        return 1 if self._intra is None else (self._buy['mv'] * self._buy['mp']).sum()
    @property
    def sellVal(self):
        return 1 if self._intra is None else (self._sell['mv'] * self._sell['mp']).sum()
    

def getAllSymbolHistory(dayNum:int=365*2+50, tickets=None, exchange: str = 'HOSE HNX'):
    if tickets is None:
        tickets = StockAPI.getAllTickets(exchange)
    print("Getting price history of %d Stocks ..." % len(tickets), end="", flush=True)
    price = {}
    cnt = 10
    for tic in tickets:
        symbol = SymbolHistory(tic, StockAPI.getPriceHistory(tic, dayNum))
        price[tic] = symbol
        cnt -= 1
        if cnt == 0:
            print(".", end="", flush=True)
            cnt = 10
    print(" Done")
    return price
    