"""Editable .xlsx, explicit linked formulas with Python-calculated cached results."""
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
from ingest import ROOT
from forecast import forecast,scenario_drivers

ROWS={k:i+5 for i,k in enumerate(['revenue','cogs','gross_profit','opex','ebit','interest','other_nonoperating','pretax','tax','net_income','cash','ar','inventory','ppe','intangibles','other_assets','assets','ap','deferred_revenue','debt','lease','other_liabilities','liabilities','equity','dep','amort','sbc','wc_cash','cfo','capex','fcf','lease_add','lease_pay','dividends','buybacks','pre_funding_cash','new_debt','cfi','cff','fx','cash_change','balance_check','cashflow_check'])}
NAMES={'revenue':'Revenue','cogs':'Cost of revenue','gross_profit':'Gross profit','opex':'Operating expenses','ebit':'Operating income / EBIT','interest':'Interest expense (blended proxy)','other_nonoperating':'Other nonoperating income','pretax':'Pretax income','tax':'Income tax','net_income':'Net income','cash':'Cash & equivalents','ar':'Accounts receivable','inventory':'Inventory','ppe':'PP&E, net','intangibles':'Finite-lived intangibles, net','other_assets':'Other assets incl. securities & goodwill','assets':'TOTAL ASSETS','ap':'Accounts payable','deferred_revenue':'Deferred revenue, current + noncurrent','debt':'Long-term debt, incl. current & new borrowing','lease':'Finance lease liabilities','other_liabilities':'Other liabilities','liabilities':'TOTAL LIABILITIES','equity':'TOTAL EQUITY','dep':'Depreciation (operating cost already in EBIT)','amort':'Intangible amortization (already in EBIT)','sbc':'Stock compensation','wc_cash':'Operating working capital cash change','cfo':'OPERATING CASH FLOW','capex':'Cash capital expenditures (positive outflow)','fcf':'FREE CASH FLOW = CFO - cash capex','lease_add':'Noncash finance lease additions','lease_pay':'Finance lease principal paid','dividends':'Cash dividends (positive outflow)','buybacks':'Cash buybacks (positive outflow)','pre_funding_cash':'Cash before minimum liquidity funding','new_debt':'New modeled borrowing to cash floor','cfi':'INVESTING CASH FLOW','cff':'FINANCING CASH FLOW','fx':'FX effect on cash','cash_change':'NET CASH CHANGE','balance_check':'CHECK: Assets - liabilities - equity','cashflow_check':'CHECK: Cash rollforward residual'}

def workbook(data,facts):
 from build import LABELS,BASIS
 w=xlsxwriter.Workbook(ROOT/'models/financial_model.xlsx')
 w.set_properties({'title':'Microsoft | Financial Lens','comments':'Independent public-data educational financial model. USD millions. No investment advice.'})
 navy='#152A28';green='#13786C';muted='#647775';teal='#E6F3EE'
 title=w.add_format({'bold':True,'font_size':21,'font_color':navy})
 head=w.add_format({'bold':True,'bg_color':navy,'font_color':'white','text_wrap':True})
 text=w.add_format({'font_color':navy});num=w.add_format({'num_format':'#,##0.0;[Red](#,##0.0);–','font_color':navy})
 formula=w.add_format({'num_format':'#,##0.0;[Red](#,##0.0);–','font_color':green,'bg_color':'#F1F8F4'})
 inp=w.add_format({'num_format':'0.0%','font_color':'#1760BB','bg_color':'#EEF5FE'})
 inpnum=w.add_format({'num_format':'0.0','font_color':'#1760BB','bg_color':'#EEF5FE'})
 pct=w.add_format({'num_format':'0.0%','font_color':navy})
 note=w.add_format({'font_color':muted,'text_wrap':True,'valign':'top'})
 total=w.add_format({'bold':True,'num_format':'#,##0.0;[Red](#,##0.0);–','font_color':green,'bg_color':teal,'top':1,'top_color':'#B5CFC5'})
 intro=w.add_worksheet('Read me');intro.set_column('A:A',4);intro.set_column('B:H',18)
 intro.merge_range('B2:H3','FINANCIAL LENS / MICROSOFT',title)
 notes=[('Scope','FY2022–26 actuals; FY2027–29 projected. Fiscal year ends June 30. USD millions.'),('Edit the model','Change blue cells on Assumptions. Base, Upside and Downside sheets recalculate all three statements. Green cells are formulas.'),('Source policy','Raw facts sheet links every selected original annual fact to SEC filing index. History excludes later-restated comparators. Warmup FY2019–21 retained in source files.'),('Method','Revenue growth: two-growth mean. Margins, tax and SBC: three-year mean. Remaining ratios: latest year. Base other nonoperating income is zero.'),('Funding','Cash is calculated from cash flow. Explicit new borrowing funds a FY2026 cash floor. Interest uses opening debt and finance leases; no circularity. Principal of existing long-term debt is held constant.'),('Leases','Noncash lease additions increase PP&E and lease debt; principal payments reduce both cash and lease debt. FCF excludes finance lease additions/principal under CFO minus cash capex convention.'),('Limitations','Aggregate annual model. No segment forecast, acquisition plan, debt maturity schedule, new operating leases, deferred-tax forecast or securities sales. Other assets/liabilities fixed. Marketable securities remain in other assets. Depreciation is a ratio proxy.'),('Backtest','Four one-year holdouts FY2023–26. Uses annual filings available on each origin date; comparator is prior-year target-metric growth. Retrospective model development may contain researcher hindsight. No tuning to holdouts.'),('Checks','Tolerance: $0.01m. Balance identity, cash linkage, PP&E, equity and date controls. A balanced model does not validate the economic assumptions.'),('Status','Independent educational portfolio analysis; not company guidance or investment advice. Power BI .pbix and GitHub publication are not included. The browser dashboard and PDF are accessible equivalents.'),('As of',data['as_of'])]
 for i,(label,value) in enumerate(notes):
  row=5+i*3;intro.write(row,1,label,head);intro.merge_range(row,2,row+1,7,value,note)
 raw=w.add_worksheet('Raw facts');raw.freeze_panes(4,2);raw.set_column(0,0,9);raw.set_column(1,1,23);raw.set_column(2,2,18);raw.set_column(3,6,23);raw.set_column(7,7,72)
 raw.merge_range('A1:H2','SOURCE FACTS / original annual filings',title)
 raw.write_row(3,0,['FY','Metric','USD millions','Tag','Accession','Period end','Filed','SEC filing'],head)
 raw_lookup={}
 for i,r in enumerate(facts,4):
  raw.write_row(i,0,[r['year'],r['field'],r['value'],r['tag'],r['accession'],r['end'],r['filed']]);raw.write_number(i,2,r['value'],num);raw.write_url(i,7,r['source_url'],string='Open filing');raw_lookup[(r['year'],r['field'])]=i+1
 raw.autofilter(3,0,len(facts)+3,7)
 actual=w.add_worksheet('Actuals');actual.set_column(0,0,48);actual.set_column(1,8,16);actual.freeze_panes(5,1)
 actual.merge_range('A1:F2','REPORTED HISTORY / USD millions',title)
 years=data['all_history']
 for j,r in enumerate(years,1):actual.write(4,j,f"FY{r['year']}A",head)
 def cell(c,k):return f'{c}{ROWS[k]+1}'
 for k,row in ROWS.items():actual.write(row,0,NAMES[k],text)
 for j,r in enumerate(years,1):
  c=xl_col_to_name(j);prev=xl_col_to_name(j-1)
  for k,row in ROWS.items():
   value=r.get(k,0)
   if k in ['wc_cash','pre_funding_cash','new_debt']:actual.write_blank(row,j,None,note);continue
   expr=None
   if (r['year'],k) in raw_lookup:expr=f"='Raw facts'!C{raw_lookup[(r['year'],k)]}"
   else:
    formulas={'debt':f"'Raw facts'!C{raw_lookup[(r['year'],'debt_current')]}+'Raw facts'!C{raw_lookup[(r['year'],'debt_noncurrent')]}",'other_assets':f"{cell(c,'assets')}-SUM({cell(c,'cash')}:{cell(c,'intangibles')})",'other_liabilities':f"{cell(c,'liabilities')}-SUM({cell(c,'ap')}:{cell(c,'lease')})",'gross_profit':f"{cell(c,'revenue')}-{cell(c,'cogs')}",'opex':f"{cell(c,'gross_profit')}-{cell(c,'ebit')}",'fcf':f"{cell(c,'cfo')}-{cell(c,'capex')}",'other_nonoperating':f"{cell(c,'pretax')}-{cell(c,'ebit')}+{cell(c,'interest')}",'balance_check':f"{cell(c,'assets')}-{cell(c,'liabilities')}-{cell(c,'equity')}",'cashflow_check':f"{cell(c,'cash_change')}-{cell(c,'cfo')}-{cell(c,'cfi')}-{cell(c,'cff')}-{cell(c,'fx')}"}
    if k in formulas:expr='='+formulas[k]
   if expr:actual.write_formula(row,j,expr,num,value)
   else:actual.write_number(row,j,value,num)
 a=w.add_worksheet('Assumptions');a.set_column('A:A',43);a.set_column('B:D',17);a.set_column('E:E',110)
 a.merge_range('A1:E2','DRIVER REGISTER / blue cells are editable',title)
 a.write_row(4,0,['Assumption','Base','Upside','Downside','Historical basis / analyst judgment'],head)
 dr={}
 for i,(k,v) in enumerate(data['drivers'].items(),5):
  dr[k]=i+1;a.write(i,0,LABELS[k],text)
  for j,s in enumerate(['base','upside','downside'],1):a.write_number(i,j,scenario_drivers(data['drivers'],s)[k],inpnum if k in ['dso','dio','dpo','cash_floor'] else inp)
  a.write(i,4,BASIS[k],note)
  for j in [1,2,3]:a.write_comment(i,j,BASIS[k]+'\nChanged: '+data['as_of']+'\nOwner: project analyst')
  for j in [1,2,3]:
   if k=='cash_floor':opts={'validate':'decimal','criteria':'>=','value':0}
   elif k in ['dso','dio','dpo']:opts={'validate':'decimal','criteria':'between','minimum':0,'maximum':365}
   elif k=='growth':opts={'validate':'decimal','criteria':'between','minimum':-.9,'maximum':1}
   else:opts={'validate':'decimal','criteria':'between','minimum':0,'maximum':1}
   a.data_validation(i,j,i,j,opts)
 a.freeze_panes(5,1)
 def formulas(c,p,A):
  C=lambda k:cell(c,k);P=lambda k:cell(p,k)
  return {
   'revenue':f"{P('revenue')}*(1+{A('growth')})",'gross_profit':f"{C('revenue')}*{A('gross_margin')}",'cogs':f"{C('revenue')}-{C('gross_profit')}",'ebit':f"{C('revenue')}*{A('margin')}",'opex':f"{C('gross_profit')}-{C('ebit')}",'interest':f"({P('debt')}+{P('lease')})*{A('interest_rate')}",'other_nonoperating':'0','pretax':f"{C('ebit')}-{C('interest')}",'tax':f"MAX(0,{C('pretax')})*{A('tax_rate')}",'net_income':f"{C('pretax')}-{C('tax')}",
   'ar':f"{C('revenue')}*{A('dso')}/365",'inventory':f"{C('cogs')}*{A('dio')}/365",'ap':f"{C('cogs')}*{A('dpo')}/365",'deferred_revenue':f"{C('revenue')}*{A('defrev_rate')}",'dep':f"{P('ppe')}*{A('dep_rate')}",'amort':f"{P('intangibles')}*{A('amort_rate')}",'capex':f"{C('revenue')}*{A('capex_rate')}",'lease_add':f"{C('revenue')}*{A('lease_add_rate')}",'lease_pay':f"{P('lease')}*{A('lease_pay_rate')}",'lease':f"{P('lease')}+{C('lease_add')}-{C('lease_pay')}",'sbc':f"{C('revenue')}*{A('sbc_rate')}",'ppe':f"{P('ppe')}+{C('capex')}+{C('lease_add')}-{C('dep')}",'intangibles':f"{P('intangibles')}-{C('amort')}",'other_assets':P('other_assets'),'other_liabilities':P('other_liabilities'),
   'wc_cash':f"-({C('ar')}-{P('ar')})-({C('inventory')}-{P('inventory')})+({C('ap')}-{P('ap')})+({C('deferred_revenue')}-{P('deferred_revenue')})",'cfo':f"{C('net_income')}+{C('dep')}+{C('amort')}+{C('sbc')}+{C('wc_cash')}",'fcf':f"{C('cfo')}-{C('capex')}",'dividends':f"MAX(0,{C('net_income')})*{A('dividend_rate')}",'buybacks':f"MAX(0,{C('net_income')})*{A('buyback_rate')}",'pre_funding_cash':f"{P('cash')}+{C('fcf')}-{C('lease_pay')}-{C('dividends')}-{C('buybacks')}",'new_debt':f"MAX(0,{A('cash_floor')}-{C('pre_funding_cash')})",'debt':f"{P('debt')}+{C('new_debt')}",'cfi':f"-{C('capex')}",'cff':f"{C('new_debt')}-{C('lease_pay')}-{C('dividends')}-{C('buybacks')}",'fx':'0','cash_change':f"{C('cfo')}+{C('cfi')}+{C('cff')}",'cash':f"{P('cash')}+{C('cash_change')}",'equity':f"{P('equity')}+{C('net_income')}+{C('sbc')}-{C('dividends')}-{C('buybacks')}",'assets':f"SUM({C('cash')}:{C('other_assets')})",'liabilities':f"SUM({C('ap')}:{C('other_liabilities')})",'balance_check':f"{C('assets')}-{C('liabilities')}-{C('equity')}",'cashflow_check':f"{C('cash')}-{P('cash')}-{C('cfo')}-{C('cfi')}-{C('cff')}"}
 for si,s in enumerate(['base','upside','downside'],1):
  sheet=w.add_worksheet(s.title());sheet.set_column(0,0,48);sheet.set_column(1,8,17);sheet.freeze_panes(5,6)
  sheet.merge_range('A1:I2',s.upper()+' / integrated statements · USD millions',title)
  sheet.merge_range('A3:I3','FY ends June 30. A = reported actual. F = analyst forecast. Positive capex / distributions are outflows.',note)
  for k,row in ROWS.items():sheet.write(row,0,NAMES[k],head if k in ['revenue','net_income','assets','liabilities','cfo','fcf','balance_check','cashflow_check'] else text)
  for j,r in enumerate(data['history']+data['scenarios'][s],1):
   c=xl_col_to_name(j);p=xl_col_to_name(j-1);sheet.write(4,j,f"FY{r['year']}{'A' if j<6 else 'F'}",head)
   fs=formulas(c,p,lambda k:f"Assumptions!${xl_col_to_name(si)}${dr[k]}") if j>=6 else {}
   for k,row in ROWS.items():
    val=r.get(k,0)
    if j<6:
     if k in ['wc_cash','pre_funding_cash','new_debt']:sheet.write_blank(row,j,None,note);continue
     expr=f"=Actuals!{xl_col_to_name(j+3)}{row+1}"
    else:expr='='+fs[k]
    sheet.write_formula(row,j,expr,total if k in ['revenue','net_income','assets','liabilities','cfo','fcf'] else formula if j>=6 else num,val)
  sheet.conditional_format(ROWS['balance_check'],6,ROWS['cashflow_check'],8,{'type':'cell','criteria':'not between','minimum':-.01,'maximum':.01,'format':w.add_format({'bg_color':'#FFC9C9'})})
  sheet.set_landscape();sheet.fit_to_pages(1,1);sheet.set_paper(9);sheet.print_area(0,0,ROWS['cashflow_check'],8)
 se=w.add_worksheet('Sensitivities');se.set_column(0,0,34);se.set_column(1,5,18);se.merge_range('A1:F2','FY2027 / two-variable sensitivities',title)
 se.merge_range('A3:F3','Each table recomputes a one-year outcome; row and column inputs link to Base assumptions.',note)
 for b,metric in enumerate(['ebit','net_income','fcf']):
  start=5+b*9;se.write(start,0,f'Growth × EBIT margin → {metric.upper()}',head)
  for j in range(5):se.write_formula(start+1,j+1,f'=Assumptions!$B${dr["margin"]}+{(j-2)*.01}',pct,data['drivers']['margin']+(j-2)*.01)
  for i in range(5):
   se.write_formula(start+i+2,0,f'=Assumptions!$B${dr["growth"]}+{(i-2)*.02}',pct,data['drivers']['growth']+(i-2)*.02)
   for j in range(5):
    A=lambda k:f'Assumptions!$B${dr[k]}'
    rev=f"(Base!$F${ROWS['revenue']+1}*(1+$A{start+i+3}))";margin=f'{xl_col_to_name(j+1)}${start+2}'
    pretax=f'({rev}*{margin}-Base!$G${ROWS["interest"]+1})'
    ni=f'({pretax}-MAX(0,{pretax})*{A("tax_rate")})'
    wc=f'-({rev}*{A("dso")}/365-Base!$F${ROWS["ar"]+1})-({rev}*(1-{A("gross_margin")} )*{A("dio")}/365-Base!$F${ROWS["inventory"]+1})+({rev}*(1-{A("gross_margin")} )*{A("dpo")}/365-Base!$F${ROWS["ap"]+1})+({rev}*{A("defrev_rate")}-Base!$F${ROWS["deferred_revenue"]+1})'
    expr=rev+'*'+margin if metric=='ebit' else ni if metric=='net_income' else f'{ni}+Base!$G${ROWS["dep"]+1}+Base!$G${ROWS["amort"]+1}+{rev}*{A("sbc_rate")}+({wc})-{rev}*{A("capex_rate")}'
    value=next(r[metric] for r in data['sensitivities'] if r['kind']=='growth_margin' and abs(r['x']-(data['drivers']['growth']+(i-2)*.02))<1e-8 and abs(r['y']-(data['drivers']['margin']+(j-2)*.01))<1e-8)
    se.write_formula(start+i+2,j+1,'='+expr,num,value)
  se.conditional_format(start+2,1,start+6,5,{'type':'3_color_scale','min_color':'#F5D6C8','mid_color':'#F4F7F4','max_color':'#72BC9E'})
 start=34;se.write(start,0,'DSO × cash capex → FCF',head)
 for j in range(5):se.write_formula(start+1,j+1,f'=Assumptions!$B${dr["capex_rate"]}+{(j-2)*.02}',pct,data['drivers']['capex_rate']+(j-2)*.02)
 for i in range(5):
  se.write_formula(start+i+2,0,f'=Assumptions!$B${dr["dso"]}+{(i-2)*5}',num,data['drivers']['dso']+(i-2)*5)
  for j in range(5):
   expr=f'=Base!$G${ROWS["fcf"]+1}-Base!$G${ROWS["revenue"]+1}*($A{start+i+3}-Assumptions!$B${dr["dso"]})/365-Base!$G${ROWS["revenue"]+1}*({xl_col_to_name(j+1)}${start+2}-Assumptions!$B${dr["capex_rate"]})'
   value=next(r['fcf'] for r in data['sensitivities'] if r['kind']=='working_capital_capex' and abs(r['x']-(data['drivers']['dso']+(i-2)*5))<1e-8 and abs(r['y']-(data['drivers']['capex_rate']+(j-2)*.02))<1e-8)
   se.write_formula(start+i+2,j+1,expr,num,value)
 se.conditional_format(start+2,1,start+6,5,{'type':'3_color_scale','min_color':'#F5D6C8','mid_color':'#F4F7F4','max_color':'#72BC9E'})
 bt=w.add_worksheet('Backtest');bt.set_column('A:M',18);bt.merge_range('A1:M2','ROLLING HOLDOUT / one year ahead',title)
 keys=list(data['backtest'][0]);bt.write_row(4,0,keys,head)
 for i,r in enumerate(data['backtest'],5):bt.write_row(i,0,list(r.values()))
 bt.merge_range('A20:M22',data['protocol']+' Baseline gap is positive when the model has a smaller MAE. Four points per metric; not evidence of statistical significance. Values are frozen evaluation outputs; rerun Python after altering model logic.',note)
 ck=w.add_worksheet('Audit checks');ck.set_column('A:A',48);ck.set_column('B:B',12);ck.set_column('C:C',100);ck.merge_range('A1:C2','QUALITY GATES / tolerance $0.01m',title);ck.write_row(4,0,['Check','Passed','Evidence'],head)
 for i,r in enumerate(data['checks'],5):ck.write_row(i,0,[r['check'],'PASS' if r['passed'] else 'FAIL',r['detail']])
 ck.write(len(data['checks'])+7,0,'Live workbook balance checks',head)
 for i,s in enumerate(['Base','Upside','Downside'],len(data['checks'])+9):
  ck.write(i,0,s+' all forecast years')
  ck.write_formula(i,1,f'=IF(MAX(ABS({s}!G{ROWS["balance_check"]+1}),ABS({s}!H{ROWS["balance_check"]+1}),ABS({s}!I{ROWS["balance_check"]+1}))<0.01,"PASS","FAIL")',text,'PASS')
 w.close()
