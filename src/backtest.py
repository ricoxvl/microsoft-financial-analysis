"""Fixed expanding-window one-year holdouts FY2023–26; FY2019–22 warmup.
Use original annual filings available at origin filing date. Protocol is specified
before results are calculated; retrospective development still has researcher
hindsight risk. Four origins do not establish statistical forecasting skill.
"""
from forecast import drivers,forecast
from statistics import mean

def backtest(history):
 rows=[]
 for year in range(2022,2026):
  train=[r for r in history if r['year']<=year]
  origin=train[-1]['filed']
  assert all(r['filed']<=origin for r in train)
  pred=forecast(train[-1],drivers(train),1)[0]
  actual=next(r for r in history if r['year']==year+1)
  for metric in ['revenue','ebit','fcf']:
   # Baseline: last observed annual growth in the target metric, no tuning.
   prior,latest=train[-2][metric],train[-1][metric]
   baseline=latest*(latest/prior) if prior else latest
   a=actual[metric];p=pred[metric]
   rows.append({'origin_year':year,'as_of':origin,'target_year':year+1,'metric':metric,'actual':a,'forecast':p,'baseline':baseline,'error':p-a,'absolute_error':abs(p-a),'ape':abs(p-a)/abs(a) if a else None,'baseline_absolute_error':abs(baseline-a),'latest_input_filed':max(r['filed'] for r in train)})
 summary=[]
 for metric in ['revenue','ebit','fcf']:
  rs=[r for r in rows if r['metric']==metric];mae=mean(r['absolute_error'] for r in rs);b=mean(r['baseline_absolute_error'] for r in rs)
  summary.append({'metric':metric,'n':len(rs),'mae':mae,'baseline_mae':b,'mape':mean(r['ape'] for r in rs),'wape':sum(r['absolute_error'] for r in rs)/sum(abs(r['actual']) for r in rs),'bias':mean(r['error'] for r in rs),'baseline_gap':b-mae,'mae_improvement':1-mae/b})
 return rows,summary
