
import StockAPI
import pickle

_DIRNAME = "data/EOD"
_TRADEDAYS = None

def getPrice(ticket:str, dayNum:int=100, resol="D"):
    fname = "%s/%s/%s/EOD-%s.pkl" % (_DIRNAME, ticket[0].lower(), ticket, resol)
    try:
        eod = pickle.load(open(fname, 'rb'))
        return eod
    except:
        pass

    eod = StockAPI.getPriceHistory("HAP", 11, resol='1',  provider='ssi')