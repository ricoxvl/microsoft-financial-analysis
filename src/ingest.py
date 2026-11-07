"""SEC annual facts, original-filing provenance, USD millions. Standard library only."""
import json, pathlib, urllib.request, hashlib,os
ROOT = pathlib.Path(__file__).resolve().parents[1]
URL = 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json'
AS_OF = '2026-11-07'
TAGS = {
 'revenue':['RevenueFromContractWithCustomerExcludingAssessedTax','SalesRevenueNet'],
 'cogs':['CostOfGoodsAndServicesSold','CostOfRevenue'],
 'ebit':['OperatingIncomeLoss'], 'net_income':['NetIncomeLoss'],
 'tax':['IncomeTaxExpenseBenefit'],
 'pretax':['IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest','IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments'],
 'interest':['InterestExpenseNonoperating','InterestExpense'],
 'cash':['CashAndCashEquivalentsAtCarryingValue'], 'ar':['AccountsReceivableNetCurrent'],
 'inventory':['InventoryNet'], 'ppe':['PropertyPlantAndEquipmentNet'],
 'intangibles':['FiniteLivedIntangibleAssetsNet'], 'assets':['Assets'],
 'ap':['AccountsPayableCurrent'], 'deferred_revenue':['ContractWithCustomerLiability','DeferredRevenue'],
 'debt_current':['LongTermDebtCurrent'], 'debt_noncurrent':['LongTermDebtNoncurrent'],
 'lease':['FinanceLeaseLiability'], 'liabilities':['Liabilities'], 'equity':['StockholdersEquity'],
 'cfo':['NetCashProvidedByUsedInOperatingActivities'],
 'capex':['PaymentsToAcquirePropertyPlantAndEquipment'],
 'cfi':['NetCashProvidedByUsedInInvestingActivities'],
 'cff':['NetCashProvidedByUsedInFinancingActivities'],
 'fx':['EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations','EffectOfExchangeRateOnCashAndCashEquivalents'],
 'cash_change':['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect','CashAndCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect'],
 'dep':['Depreciation'], 'amort':['AmortizationOfIntangibleAssets'],
 'sbc':['ShareBasedCompensation'], 'dividends':['PaymentsOfDividendsCommonStock'],
 'buybacks':['PaymentsForRepurchaseOfCommonStock'],
 'lease_add':['RightOfUseAssetObtainedInExchangeForFinanceLeaseLiability'],
 'lease_pay':['FinanceLeasePrincipalPayments']
}
INSTANT = {'cash','ar','inventory','ppe','intangibles','assets','ap','deferred_revenue','debt_current','debt_noncurrent','lease','liabilities','equity'}

def fetch():
 p=ROOT/'data/raw/companyfacts.json'
 identity=os.environ.get('SEC_USER_AGENT')
 if not identity:raise ValueError('Set SEC_USER_AGENT to your research identity and contact email before refreshing SEC data.')
 req=urllib.request.Request(URL,headers={'User-Agent':identity})
 data=urllib.request.urlopen(req,timeout=60).read()
 if p.exists():
  digest=hashlib.sha256(p.read_bytes()).hexdigest()[:16]
  archive=p.with_name('companyfacts_'+digest+'.json')
  if not archive.exists():archive.write_bytes(p.read_bytes())
 p.write_bytes(data)

def normalize(as_of=AS_OF):
 facts=json.loads((ROOT/'data/raw/companyfacts.json').read_text())['facts']['us-gaap']
 rows=[]; history=[]
 for year in range(2019,2027):
  end=f'{year}-06-30'; start=f'{year-1}-07-01'; r={'year':year}
  for field,tags in TAGS.items():
   choices=[]
   for priority,tag in enumerate(tags):
    for f in facts.get(tag,{}).get('units',{}).get('USD',[]):
     if f.get('form')!='10-K' or f['end']!=end or f.get('filed','9999')>as_of:continue
     if field in INSTANT:
      if f.get('start'):continue
     elif f.get('start')!=start:continue
     choices.append((f['filed'],priority,tag,f))
   if not choices:raise ValueError(f'Missing required SEC fact: {year} {field}')
   # First available annual filing, never latest restated comparator.
   filed,_,tag,f=sorted(choices,key=lambda x:(x[0],x[1]))[0]
   r[field]=f['val']/1e6
   accn=f['accn']; url=f'https://www.sec.gov/Archives/edgar/data/789019/{accn.replace("-", "")}/{accn}-index.html'
   rows.append({'year':year,'field':field,'value':r[field],'unit':'USD millions','namespace':'us-gaap','tag':tag,'form':'10-K','accession':accn,'start':'' if field in INSTANT else start,'end':end,'filed':filed,'source_url':url,'api_url':URL,'retrieved':AS_OF})
  r['filed']=max(x['filed'] for x in rows if x['year']==year)
  r['debt']=r['debt_current']+r['debt_noncurrent']
  r['other_assets']=r['assets']-sum(r[k] for k in ['cash','ar','inventory','ppe','intangibles'])
  r['other_liabilities']=r['liabilities']-sum(r[k] for k in ['ap','deferred_revenue','debt','lease'])
  r['gross_profit']=r['revenue']-r['cogs'];r['opex']=r['gross_profit']-r['ebit']
  r['fcf']=r['cfo']-r['capex'];r['other_nonoperating']=r['pretax']-r['ebit']+r['interest']
  r['balance_check']=r['assets']-r['liabilities']-r['equity']
  r['cashflow_check']=r['cash_change']-r['cfo']-r['cfi']-r['cff']-r['fx']
  history.append(r)
 return history,rows

if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--refresh',action='store_true');args=a.parse_args()
 if args.refresh:fetch()
 h,r=normalize();print(json.dumps(h,indent=2))
