"""Integrated annual operating model. All monetary values USD millions.

Cash is a cash-flow result. A disclosed minimum-cash revolver rule funds shortfalls.
No debt/interest circularity: interest uses opening interest-bearing liabilities.
"""
from statistics import mean

def drivers(history):
 recent=history[-3:];last=history[-1]
 growth=mean(history[i]['revenue']/history[i-1]['revenue']-1 for i in range(len(history)-2,len(history)))
 return {
  'growth':growth,'margin':mean(x['ebit']/x['revenue'] for x in recent),
  'gross_margin':mean(1-x['cogs']/x['revenue'] for x in recent),
  'tax_rate':mean(x['tax']/x['pretax'] for x in recent),
  'capex_rate':last['capex']/last['revenue'],
  'dso':last['ar']/last['revenue']*365,'dio':last['inventory']/last['cogs']*365,
  'dpo':last['ap']/last['cogs']*365,
  'defrev_rate':last['deferred_revenue']/last['revenue'],
  'dep_rate':last['dep']/last['ppe'],
  'amort_rate':last['amort']/last['intangibles'],
  'sbc_rate':mean(x['sbc']/x['revenue'] for x in recent),
  'interest_rate':last['interest']/(last['debt']+last['lease']),
  'dividend_rate':last['dividends']/last['net_income'],
  'buyback_rate':last['buybacks']/last['net_income'],
  'lease_add_rate':last['lease_add']/last['revenue'],
  'lease_pay_rate':last['lease_pay']/last['lease'],
  'cash_floor':last['cash']
 }

def scenario_drivers(d,scenario):
 a=dict(d)
 # Judgment shocks, separate from historical anchors; not management guidance.
 if scenario=='upside':
  a['growth']+=.03;a['margin']+=.02;a['dso']-=3;a['capex_rate']-=.02
 elif scenario=='downside':
  a['growth']-=.05;a['margin']-=.03;a['dso']+=5;a['capex_rate']+=.02
 return a

def forecast(last,d,years=3):
 out=[];p=last
 for _ in range(years):
  r={'year':p['year']+1,'forecast':True}
  r['revenue']=p['revenue']*(1+d['growth'])
  r['gross_profit']=r['revenue']*d['gross_margin'];r['cogs']=r['revenue']-r['gross_profit']
  r['ebit']=r['revenue']*d['margin'];r['opex']=r['gross_profit']-r['ebit']
  r['interest']=(p['debt']+p['lease'])*d['interest_rate']
  r['other_nonoperating']=0;r['pretax']=r['ebit']-r['interest']
  r['tax']=max(0,r['pretax'])*d['tax_rate'];r['net_income']=r['pretax']-r['tax']
  r['ar']=r['revenue']*d['dso']/365;r['inventory']=r['cogs']*d['dio']/365
  r['ap']=r['cogs']*d['dpo']/365;r['deferred_revenue']=r['revenue']*d['defrev_rate']
  r['dep']=p['ppe']*d['dep_rate'];r['amort']=p['intangibles']*d['amort_rate']
  r['capex']=r['revenue']*d['capex_rate'];r['lease_add']=r['revenue']*d['lease_add_rate']
  r['lease_pay']=p['lease']*d['lease_pay_rate'];r['lease']=p['lease']+r['lease_add']-r['lease_pay']
  r['sbc']=r['revenue']*d['sbc_rate']
  r['ppe']=p['ppe']+r['capex']+r['lease_add']-r['dep']
  r['intangibles']=p['intangibles']-r['amort']
  r['other_assets']=p['other_assets'];r['other_liabilities']=p['other_liabilities']
  r['wc_cash']=-(r['ar']-p['ar'])-(r['inventory']-p['inventory'])+(r['ap']-p['ap'])+(r['deferred_revenue']-p['deferred_revenue'])
  r['cfo']=r['net_income']+r['dep']+r['amort']+r['sbc']+r['wc_cash']
  r['fcf']=r['cfo']-r['capex'];r['dividends']=max(0,r['net_income'])*d['dividend_rate']
  r['buybacks']=max(0,r['net_income'])*d['buyback_rate']
  r['pre_funding_cash']=p['cash']+r['fcf']-r['lease_pay']-r['dividends']-r['buybacks']
  r['new_debt']=max(0,d['cash_floor']-r['pre_funding_cash'])
  r['debt']=p['debt']+r['new_debt'];r['cfi']=-r['capex']
  r['cff']=r['new_debt']-r['lease_pay']-r['dividends']-r['buybacks'];r['fx']=0
  r['cash_change']=r['cfo']+r['cfi']+r['cff'];r['cash']=p['cash']+r['cash_change']
  r['equity']=p['equity']+r['net_income']+r['sbc']-r['dividends']-r['buybacks']
  r['assets']=sum(r[k] for k in ['cash','ar','inventory','ppe','intangibles','other_assets'])
  r['liabilities']=sum(r[k] for k in ['ap','deferred_revenue','debt','lease','other_liabilities'])
  r['balance_check']=r['assets']-r['liabilities']-r['equity']
  r['cashflow_check']=r['cash']-p['cash']-r['cfo']-r['cfi']-r['cff']
  out.append(r);p=r
 return out
