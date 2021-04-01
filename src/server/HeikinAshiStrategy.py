import numpy as np
from StrategyCommon import Decision

def heikin_ashi_stochrsi_decision(ha, rsi, ma5, ma10, idx=-1):
    rsi = rsi.iloc[idx]
    ma5 = ma5.iloc[idx]
    ma10 = ma10.iloc[idx]
    # Look back maximum of 3 days
    def haDirCal(h):
        h2l = h['high']-h['low']
        if h['open'] < h['close']:
            if ((h['open']-h['low']) / h2l) < 0.10:
                return 'strong-bull'
            if ((h['close']-h['open']) / h2l) < 0.15:
                return 'doji-bull'
            return 'weak-bull'
        else:
            if ((h['high']-h['close']) / h2l) < 0.10:
                return 'strong-bear'
            if ((h['open']-h['close']) / h2l) < 0.15:
                return 'doji-bear'
            return 'weak-bear'
    haDir = [ haDirCal(ha.iloc[idx]), haDirCal(ha.iloc[idx-1]),
                haDirCal(ha.iloc[idx-2]), haDirCal(ha.iloc[idx-3]) ]
    
    if haDir[0] == 'strong-bull' and rsi >= 50 and ma5 >= ma10 and \
        not any([x=='strong-bull' for x in haDir[1:]]):
        return Decision.BUY, "HA show strong bull"
    if 'bear' in haDir[0] and any([x=='strong-bear' for x in haDir[1:]]) and \
        rsi <= 50 and ma5 <= ma10:
        return Decision.SELL, "HA show strong sell"
    return Decision.KEEP, "HA show no sign"
    