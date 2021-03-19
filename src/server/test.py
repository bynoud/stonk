
# weeks = 52
# selTickets = []

# days = weeks*5
# selDf = pd.DataFrame(df['date'].iloc[-days:])
# for tic in tickets:
#     if df['%s$close' % tic].count() >= days:
#         selTickets.append(tic)
#         selDf['%s$close' % tic] = df['%s$close' % tic].iloc[-days:]
#         selDf['%s$close$percent' % tic] = selDf['%s$close' % tic].pct_change(axis=0, fill_method='bfill')

corr = {}
for s1 in range(len(selTickets)):
    for s2 in range(s1+1, len(selTickets)):
            t1 = selTickets[s1]
            t2 = selTickets[s2]
            corr["%s-%s" % (t1,t2)] = selDf["%s$close$percent" % t1].corr(selDf["%s$close$percent" % t2])
