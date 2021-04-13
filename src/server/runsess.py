# run this : exec(open("runsess.py").read())
import StrategySession

def signPrint(signals):
    from StrategyCommon import Decision
    res = ''
    for tic,sig in signals.items():
        # cur += "[%s]\n" % tic
        cur = ''
        for s in sig:
            if s['dec'] != Decision.KEEP:
                if type(s['reason']) is str:
                    cur += "\t%s : %s\n" % (s['dec'], s['reason'])
                else:
                    cur += "\t%s :\n" % s['dec']
                    for reason in s['reason']:
                        cur += "\t\t+ %s\n" % reason
        if cur != '':
            res += '[%s]\n%s' % (tic, cur)
    return res

ss = StrategySession.BacktestSession()
ss.start()
signals = ss.signals
print(signPrint(signals))
