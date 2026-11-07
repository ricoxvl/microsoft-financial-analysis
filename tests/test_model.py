"""Meaningful accounting, provenance and independently parsed workbook checks."""
import unittest,sys,pathlib,json,re,math
from functools import lru_cache
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from ingest import normalize,ROOT
from forecast import drivers,forecast,scenario_drivers
from backtest import backtest
from openpyxl import load_workbook

class ModelTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.h,cls.f=normalize();cls.d=drivers(cls.h)
 def test_five_original_annual_periods_and_units(self):
  for year in range(2022,2027):
   f=[r for r in self.f if r['year']==year]
   self.assertEqual(len(f),33)
   self.assertTrue(all(r['end']==f'{year}-06-30' and r['unit']=='USD millions' for r in f))
   self.assertTrue(all(r['start'] in ['',f'{year-1}-07-01'] for r in f))
 def test_reported_reconciliation(self):
  import csv
  with open(ROOT/'results/filing_reconciliation.csv') as f:r=list(csv.DictReader(f))
  self.assertEqual(len(r),165);self.assertTrue(all(x['passed']=='True' for x in r))
  for r in self.h:
   self.assertAlmostEqual(r['assets'],r['liabilities']+r['equity'])
   self.assertAlmostEqual(r['cash_change'],r['cfo']+r['cfi']+r['cff']+r['fx'])
 def test_stress_funding_without_accounting_plug(self):
  for growth in [-.05,.1,.3]:
   for margin in [.25,.45,.6]:
    for capex in [.15,.5]:
     d={**self.d,'growth':growth,'margin':margin,'capex_rate':capex,'dso':125}
     p=self.h[-1]
     for r in forecast(p,d):
      self.assertLess(abs(r['balance_check']),.01);self.assertLess(abs(r['cashflow_check']),.01)
      self.assertGreaterEqual(r['cash'],d['cash_floor']-.01)
      self.assertAlmostEqual(r['ppe'],p['ppe']+r['capex']+r['lease_add']-r['dep'])
      self.assertAlmostEqual(r['equity'],p['equity']+r['net_income']+r['sbc']-r['dividends']-r['buybacks'])
      self.assertAlmostEqual(r['new_debt'],max(0,d['cash_floor']-r['pre_funding_cash']))
      p=r
 def test_cash_economics(self):
  b=forecast(self.h[-1],self.d,1)[0]
  c=forecast(self.h[-1],{**self.d,'capex_rate':self.d['capex_rate']+.01},1)[0]
  self.assertAlmostEqual(c['fcf']-b['fcf'],-.01*b['revenue'])
  c=forecast(self.h[-1],{**self.d,'dso':self.d['dso']+1},1)[0]
  self.assertAlmostEqual(c['fcf']-b['fcf'],-b['revenue']/365)
 def test_origin_fact_availability(self):
  b,_=backtest(self.h)
  for r in b:
   self.assertTrue(all(f['filed']<=r['as_of'] for f in self.f if f['year']<=r['origin_year']))
   self.assertEqual(r['target_year'],r['origin_year']+1)
  self.assertEqual(len(b),12)
 def test_all_workbook_formulas_against_independent_evaluation(self):
  from openpyxl.utils.cell import range_boundaries
  path=ROOT/'models/financial_model.xlsx';formula=load_workbook(path,data_only=False);cached=load_workbook(path,data_only=True)
  # Evaluate actual Excel references independently; catches cross-sheet/row errors.
  pattern=re.compile(r"(?:(?:'([^']+)'|([A-Za-z_][A-Za-z_ ]*))!)?(\$?[A-Z]{1,3}\$?\d+)(?::(\$?[A-Z]{1,3}\$?\d+))?")
  @lru_cache(None)
  def value(sheet,coord):
   v=formula[sheet][coord].value
   if not isinstance(v,str) or not v.startswith('='):return v or 0
   refs=[]
   def repl(m):
    sh=m.group(1) or m.group(2) or sheet;a=m.group(3).replace('$','');b=m.group(4)
    if b:
     x1,y1,x2,y2=range_boundaries(a+':'+b.replace('$',''))
     vals=[value(sh,formula[sh].cell(y,x).coordinate) for y in range(y1,y2+1) for x in range(x1,x2+1)]
     refs.append(vals)
    else:refs.append(value(sh,a))
    return f'R[{len(refs)-1}]'
   expr=pattern.sub(repl,v[1:])
   env={'R':refs,'SUM':lambda *a:sum(x for z in a for x in (z if isinstance(z,list) else [z])),'MAX':max,'ABS':abs,'IF':lambda cond,a,b:a if cond else b}
   return eval(expr,{'__builtins__':{}},env)
  count=0
  for sh in formula:
   for row in sh:
    for c in row:
     if c.data_type=='f':
      computed=value(sh.title,c.coordinate);expected=cached[sh.title][c.coordinate].value
      if isinstance(expected,(int,float)):
       self.assertAlmostEqual(computed,expected,places=5,msg=f'{sh.title}!{c.coordinate}')
      else:self.assertEqual(computed,expected)
      count+=1
  self.assertGreater(count,1000)

if __name__=='__main__':unittest.main(verbosity=2)
