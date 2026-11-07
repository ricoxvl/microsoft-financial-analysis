"""Rebuild processed evidence, SQLite, cached-formula workbook and dashboard data."""
import csv,json,pathlib,sqlite3,hashlib,sys
from statistics import mean
from ingest import normalize,ROOT,AS_OF,TAGS
from forecast import drivers,scenario_drivers,forecast
from backtest import backtest

LABELS={'growth':'Revenue growth','margin':'Operating margin','gross_margin':'Gross margin','tax_rate':'Effective tax rate','capex_rate':'Cash capex / revenue','dso':'Days sales outstanding','dio':'Days inventory outstanding','dpo':'Days payable outstanding','defrev_rate':'Deferred revenue / revenue','dep_rate':'Depreciation / opening PP&E','amort_rate':'Amortization / opening intangibles','sbc_rate':'Stock compensation / revenue','interest_rate':'Interest / opening debt & finance leases','dividend_rate':'Dividends / net income','buyback_rate':'Buybacks / net income','lease_add_rate':'Finance lease additions / revenue','lease_pay_rate':'Lease principal / opening finance leases','cash_floor':'Minimum cash balance ($m)'}
BASIS={k:'Latest FY2026 ratio; held constant as a simplifying planning assumption.' for k in LABELS}
BASIS.update(growth='Mean of FY2025 and FY2026 revenue growth; constant aggregate growth, no segment forecast.',margin='Mean FY2024–26 EBIT / revenue; normalizes recent operating results.',gross_margin='Mean FY2024–26 gross margin.',tax_rate='Mean FY2024–26 effective tax rate; no tax benefit on forecast losses.',sbc_rate='Mean FY2024–26 stock compensation / revenue.',cash_floor='FY2026 cash; new modeled borrowing funds shortfalls. Marketable securities are held fixed in other assets.',dep_rate='FY2026 depreciation / ending PP&E applied to future opening PP&E; approximate cohort aging.',amort_rate='FY2026 amortization / ending intangibles applied to future opening intangibles.',interest_rate='FY2026 reported nonoperating interest / ending long-term debt and finance leases; blended proxy, no explicit debt maturities.')
DIRECTION={'growth':'Higher revenue; net cash effect depends on margin, capex and WC intensity.','margin':'Higher EBIT and after-tax earnings/FCF; gross margin held fixed.','gross_margin':'At fixed EBIT margin, reallocates COGS vs opex; changes inventory/payables cash drivers.','tax_rate':'Higher tax reduces net income and CFO, absent offsetting driver changes.','capex_rate':'Higher cash capex lowers FCF and increases PP&E.','dso':'Slower collections increase receivables and reduce CFO.','dio':'Higher inventory days increase inventory and reduce CFO.','dpo':'Higher payable days increase payables and CFO.','defrev_rate':'Higher contract liabilities increase CFO as revenue grows.','dep_rate':'At fixed EBIT, increases noncash CFO adjustment and reduces net PP&E.','amort_rate':'At fixed EBIT, increases noncash CFO adjustment and reduces intangibles.','sbc_rate':'At fixed EBIT, increases noncash CFO adjustment and paid-in equity.','interest_rate':'Higher opening-balance interest reduces earnings and CFO.','dividend_rate':'Higher payouts reduce financing cash and equity.','buyback_rate':'Higher repurchases reduce financing cash and equity.','lease_add_rate':'Increases PP&E and lease liabilities; no immediate cash-capex FCF impact.','lease_pay_rate':'Reduces cash and lease liabilities; increases financing cash outflow.','cash_floor':'Higher liquidity target can require more borrowing; affects subsequent interest.'}

def csvout(path,rows):
 if not rows:return
 with open(ROOT/path,'w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
 h,facts=normalize();d=drivers(h);cases={s:forecast(h[-1],scenario_drivers(d,s)) for s in ['base','upside','downside']}
 bt,stats=backtest(h)
 checks=[]
 def check(name,value,detail):
  checks.append({'check':name,'passed':bool(value),'detail':detail})
 for r in h:
  check(f"FY{r['year']} historical balance",abs(r['balance_check'])<.01,f"Residual {r['balance_check']:.6f} USDm")
  check(f"FY{r['year']} reported cash flow",abs(r['cashflow_check'])<.01,f"Residual {r['cashflow_check']:.6f} USDm")
 for s,rs in cases.items():
  for r in rs:
   check(f"{s} FY{r['year']} balance",abs(r['balance_check'])<.01,f"Residual {r['balance_check']:.6f} USDm")
   check(f"{s} FY{r['year']} cash flow",abs(r['cashflow_check'])<.01,f"Residual {r['cashflow_check']:.6f} USDm")
   check(f"{s} FY{r['year']} cash floor",r['cash']>=d['cash_floor']-.01,'Explicit borrowing rule; interest on opening financing only')
 check('Backtest filing-date leakage',all(x['latest_input_filed']<=x['as_of'] for x in bt),'Original annual filings only; FY2023–26 held out, four origins')
 check('Scenario FCF ordering',cases['upside'][-1]['fcf']>cases['base'][-1]['fcf']>cases['downside'][-1]['fcf'],'Joint scenario shocks propagate through all statements')
 check('Forecast PP&E rollforward',all(abs(r['ppe']-p['ppe']-r['capex']-r['lease_add']+r['dep'])<.01 for rs in cases.values() for p,r in zip([h[-1]]+rs[:-1],rs)),'Cash capex plus noncash finance lease additions less depreciation')
 check('Noncash SBC equity linkage',all(abs(r['equity']-p['equity']-r['net_income']-r['sbc']+r['dividends']+r['buybacks'])<.01 for rs in cases.values() for p,r in zip([h[-1]]+rs[:-1],rs)),'Retained earnings and paid-in capital modeled in aggregate equity')
 check('Unique source facts',len(facts)==len({(r['year'],r['field']) for r in facts}),'One original-filing USD fact per year / modeled field')
 sensitivity=[]
 for kind in ['growth_margin','working_capital_capex']:
  for i in range(-2,3):
   for j in range(-2,3):
    a=dict(d)
    if kind=='growth_margin':a['growth']+=i*.02;a['margin']+=j*.01;x=a['growth'];y=a['margin']
    else:a['dso']+=i*5;a['capex_rate']+=j*.02;x=a['dso'];y=a['capex_rate']
    p=forecast(h[-1],a,1)[0]
    sensitivity.append({'kind':kind,'x':x,'y':y,'year':2027,'ebit':p['ebit'],'net_income':p['net_income'],'fcf':p['fcf'],'cash':p['cash'],'new_debt':p['new_debt']})
 for k in ['growth','margin','capex_rate','dso']:
  a=dict(d);a[k]+={'growth':.01,'margin':.01,'capex_rate':.01,'dso':1}[k]
  p=forecast(h[-1],a,1)[0]
  sensitivity.append({'kind':'driver_impact','x':k,'y':a[k]-d[k],'year':2027,'ebit':p['ebit']-cases['base'][0]['ebit'],'net_income':p['net_income']-cases['base'][0]['net_income'],'fcf':p['fcf']-cases['base'][0]['fcf'],'cash':p['cash']-cases['base'][0]['cash'],'new_debt':p['new_debt']-cases['base'][0]['new_debt']})
 register=[{'driver':k,'label':LABELS[k],'unit':'USD millions' if k=='cash_floor' else 'days' if k in ['dso','dio','dpo'] else 'ratio','base':v,'upside':scenario_drivers(d,'upside')[k],'downside':scenario_drivers(d,'downside')[k],'basis':BASIS[k],'owner':'Project analyst','last_changed':AS_OF,'direction':DIRECTION[k]} for k,v in d.items()]
 csvout('data/processed/source_facts.csv',facts);csvout('data/processed/history.csv',[{k:r.get(k,'') for k in h[0]} for r in h])
 csvout('results/forecast_errors.csv',bt);csvout('results/backtest_summary.csv',stats)
 csvout('results/sensitivities.csv',sensitivity);csvout('results/checks.csv',checks);csvout('docs/assumptions_register.csv',register)
 csvout('results/scenario_summary.csv',[dict(scenario=s,**r) for s,rs in cases.items() for r in rs])
 manifest=[]
 for year in range(2019,2027):
  r=next(x for x in facts if x['year']==year)
  manifest.append({k:r[k] for k in ['year','form','accession','filed','start','end','source_url','api_url','retrieved']})
 csvout('docs/source_manifest.csv',manifest)
 from workbook import NAMES
 dictionary=[]
 derived={'debt':'Long-term debt current + noncurrent; modeled new borrowing added in forecasts.','other_assets':'Total assets less cash, AR, inventory, PP&E and finite-lived intangibles. Includes securities, goodwill and other assets.','other_liabilities':'Total liabilities less payables, deferred revenue, long-term debt and finance lease debt.','gross_profit':'Revenue less cost of revenue.','opex':'Gross profit less operating income.','fcf':'CFO less cash capital expenditures; no deduction for noncash lease additions.','other_nonoperating':'Reported pretax less EBIT plus interest. Forecast normalized to zero.','balance_check':'Assets less liabilities less equity; $0.01m tolerance.','cashflow_check':'Historical cash change less CFO, CFI, CFF and FX. Forecast checks ending/beginning cash and flows.','wc_cash':'Negative change AR/inventory plus change AP/deferred revenue in forecast.','new_debt':'MAX(0, cash floor - cash before funding).','pre_funding_cash':'Opening cash plus FCF less lease principal, dividends and buybacks.'}
 for k in sorted(set(TAGS)|set(NAMES)):
  dictionary.append({'field':k,'description':derived.get(k,NAMES.get(k,k.replace('_',' '))),'unit':'USD millions','history_source':' | '.join(TAGS[k]) if k in TAGS else 'Derived; see description and src/forecast.py','sign':'CFI/CFF/FX signed cash flow; capex, dividends, buybacks, lease_pay and expense fields positive costs/outflows; other balance fields positive assets/liabilities except checks.'})
 csvout('docs/data_dictionary.csv',dictionary)
 raw=ROOT/'data/raw/companyfacts.json'
 (ROOT/'docs/raw_sha256.txt').write_text(hashlib.sha256(raw.read_bytes()).hexdigest()+'  data/raw/companyfacts.json\n')
 dbpath=ROOT/'data/financials.db'
 if dbpath.exists():dbpath.unlink()
 con=sqlite3.connect(dbpath)
 con.execute('CREATE TABLE source_facts (year INTEGER,field TEXT,value REAL,unit TEXT,namespace TEXT,tag TEXT,form TEXT,accession TEXT,start TEXT,end TEXT,filed TEXT,source_url TEXT,api_url TEXT,retrieved TEXT,PRIMARY KEY(year,field))')
 con.executemany('INSERT INTO source_facts VALUES ('+','.join('?'*14)+')',[list(x.values()) for x in facts])
 con.execute('CREATE VIEW annual_kpis AS SELECT year, MAX(CASE WHEN field="revenue" THEN value END) revenue, MAX(CASE WHEN field="ebit" THEN value END) ebit, MAX(CASE WHEN field="cfo" THEN value END)-MAX(CASE WHEN field="capex" THEN value END) fcf FROM source_facts GROUP BY year')
 con.commit();con.close()
 payload={'company':'Microsoft Corporation','ticker':'MSFT','cik':'0000789019','as_of':AS_OF,'history':h[-5:],'all_history':h,'drivers':d,'assumptions':register,'scenarios':cases,'backtest':bt,'backtest_summary':stats,'sensitivities':sensitivity,'checks':checks,'sources':manifest,'unit':'USD millions','fiscal_year_end':'June 30','protocol':'FY2022–25 filing-date origins; one-year FY2023–26 targets. Three-year ratio means, two-growth mean; metric-specific prior-year growth baseline. Original annual SEC facts; no later-restated comparators.'}
 (ROOT/'data/processed/model.json').write_text(json.dumps(payload,indent=2))
 from workbook import workbook
 workbook(payload,facts)
 print(json.dumps({'checks':len(checks),'passed':sum(x['passed'] for x in checks),'drivers':d,'base_2029':cases['base'][-1],'backtest':stats},indent=2))
 if not all(x['passed'] for x in checks):sys.exit(1)

if __name__=='__main__':main()
