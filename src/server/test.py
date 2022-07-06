
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def ccical(df, win=20, const=0.015):
    tp = (df.high + df.low + df.close) / 3
    mad = lambda x: np.fabs(x - x.mean()).mean()
    sma = tp.rolling(window=win)
    return (tp - sma.mean()) / (const * sma.apply(mad, raw=True))

def plot(df, win=20):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, specs=[[{"secondary_y": True}],[{"secondary_y": True}]])
    x = list(range(len(df)))

    cci = ccical(df,win)

    fig.add_trace(go.Candlestick(x=x,
        open=df.open, close=df.close,
        high=df.high, low=df.low), row=1, col=1)

    fig.add_trace(go.Scatter(x=x, y=df.abvRsi, name='ABV', mode='lines', line={'color':'green'}), secondary_y=False, row=2, col=1)
    fig.add_trace(go.Scatter(x=x, y=cci, name='CCI', mode='lines', line={'color':'blue'}), secondary_y=True, row=2, col=1)
    # fig.add_trace(go.Scatter(x=df.date, y=(df.topPossitionRatio-1)*10, name='topPossitionRatio', mode='lines', line={'color':'red'}), row=2, col=1)


    # accDiff = df.globalRatio - df.topAccountRatio
    # fig.add_trace(go.Bar(x=df.date, y=accDiff, offsetgroup=0), row=3, col=1)

    return fig