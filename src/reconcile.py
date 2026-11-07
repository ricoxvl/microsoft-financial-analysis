"""Reconcile selected annual API facts against original 10-K inline XBRL.
The filing HTML is separately archived so the API is not its own only check.
"""
import pathlib,csv,urllib.request,re,time,os
from lxml import html
from ingest import ROOT,normalize

def reconcile():
 h,facts=normalize();result=[]
 for year in range(2022,2027):
  rows=[r for r in facts if r['year']==year];accn=rows[0]['accession']
  doc=f'msft-10k_{year}0630.htm' if year<=2022 else f'msft-{year}0630.htm'
  url=f'https://www.sec.gov/Archives/edgar/data/789019/{accn.replace("-", "")}/{doc}'
  path=ROOT/f'data/raw/msft-{year}-10k.html'
  if not path.exists():
   identity=os.environ.get('SEC_USER_AGENT')
   if not identity:raise ValueError('Set SEC_USER_AGENT to your research identity and contact email to fetch missing filings.')
   req=urllib.request.Request(url,headers={'User-Agent':identity})
   path.write_bytes(urllib.request.urlopen(req,timeout=60).read());time.sleep(.2)
  tree=html.parse(str(path));contexts={}
  for c in tree.xpath('//*[name()="xbrli:context"]'):
   if c.xpath('.//*[contains(name(),"member")]'):continue
   dates={n.tag.split(':')[-1]:n.text for n in c.iter() if n.tag.split(':')[-1] in ['startdate','enddate','instant']}
   contexts[c.get('id')]=dates
  nodes=tree.xpath('//*[name()="ix:nonfraction"]')
  for r in rows:
   values=[]
   for node in nodes:
    if node.get('name')!='us-gaap:'+r['tag']:continue
    c=contexts.get(node.get('contextref'))
    if not c or c.get('instant',c.get('enddate'))!=r['end'] or (r['start'] and c.get('startdate')!=r['start']):continue
    val=node.text_content().strip().replace(',','').replace('$','').replace('(','').replace(')','').replace('\u00a0','').replace(' ','')
    if val in ['—','–','-','']:val='0'
    try:value=float(val)*10**int(node.get('scale','0'))*(-1 if node.get('sign')=='-' else 1)/1e6
    except ValueError:continue
    values.append(value)
   match=any(abs(v-r['value'])<.01 for v in values)
   result.append({'year':year,'field':r['field'],'tag':r['tag'],'api_value':r['value'],'filing_values':'|'.join(str(v) for v in sorted(set(values))),'passed':match,'source_url':url,'local_file':str(path.relative_to(ROOT))})
 with open(ROOT/'results/filing_reconciliation.csv','w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=result[0]);w.writeheader();w.writerows(result)
 print(f'{sum(r["passed"] for r in result)} / {len(result)} source fact reconciliations passed')
 for r in result:
  if not r['passed']:print(r)
 return result

if __name__=='__main__':
 result=reconcile()
 if not all(r['passed'] for r in result):raise SystemExit(1)
