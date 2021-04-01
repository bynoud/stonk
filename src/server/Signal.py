
import numpy as np
from Symbol import SymbolHistory

# def super_trend_signal(symbol: SymbolHistory) -> Decision:
#     st = Indicator.super_trend(symbol.high, symbol.low, symbol.close)
#     if st['bull'].iloc[-2] and not st['bull'].iloc[-1]:
#         return Signal.BULL
#     if 

def is_near_super_trend_support(symbol: SymbolHistory) -> bool:
    st = symbol.super_trend()
    val, bull = st['st'].iloc[-1], st['bull'].iloc[-1]
    if bull and symbol.low.iloc[-1] < val and symbol.close.iloc[-1] >= val:
        return True
    return False

def heikin_ashi_signal(symbol: SymbolHistory):
    ha = symbol.heikin_ashi()
    rsi = symbol.rsi().iloc[-1]
    ma5 = symbol.ema(5).iloc[-1]
    ma10 = symbol.ema(10).iloc[-1]
    # Look back maximum of 3 days
    def haDirCal(h):
        if h['open'] == h['low']: return 'strong-bull'
        if (np.abs(h['open']-h['close']) / (h['high']-h['low'])) < 0.15:
            return 'doji-bull' if (h['open'] <= h['close']) else 'doji-bear'
        if h['open'] > h['close']: return 'weak-bear'
        if h['open'] <= h['close']: return 'weak-bull'
        return 'none'
    haDir = [ haDirCal(ha.iloc[-1]), haDirCal(ha.iloc[-2]),
                haDirCal(ha.iloc[-3]), haDirCal(ha.iloc[-4]) ]
    
    if haDir[0] == 'strong-bull' and rsi >= 50 and ma5 >= ma10 and \
        not any([x=='strong-bull' for x in haDir[1:]]):
        return 'bull'
    if 'bear' in haDir[0] and any([x=='strong-bear' for x in haDir[1:]]) and \
        rsi <= 50 and ma5 <= ma10:
        return 'bear'
    return 'none' 
    