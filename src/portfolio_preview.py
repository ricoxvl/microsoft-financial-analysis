"""Optional README chart, rendered from model outputs rather than a mock screenshot.
Install requirements-preview.txt to regenerate. Main analysis does not need matplotlib.
"""
import json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=pathlib.Path(__file__).resolve().parents[1]

def main():
 j=json.loads((ROOT/'data/processed/model.json').read_text());h=j['history'];f=j['scenarios']['base'];r=h[-1]
 bg='#f4f7f0';ink='#203f32';muted='#788b72';green='#416b4c';mint='#b6c9a8';gold='#b09256';line='#dce5d4'
 fig=plt.figure(figsize=(14,8),facecolor=bg)
 fig.text(.06,.94,'MICROSOFT  /  FINANCIAL LENS',fontweight='bold',fontsize=10,color=muted)
 fig.text(.06,.875,'Growth is strong. Cash needs a closer look.',fontweight='bold',fontsize=24,color=ink)
 fig.text(.06,.83,'Five years of reported performance. Three years of conditional forecasts.',fontsize=11,color=muted)
 for x,label,value,note in [(.06,'FY2026 REVENUE',f'${r["revenue"]/1000:.1f}B','Reported actual'),(.365,'FY2026 OPERATING MARGIN',f'{r["ebit"]/r["revenue"]*100:.1f}%','Reported actual'),(.67,'FY2026 FREE CASH FLOW',f'${r["fcf"]/1000:.1f}B','CFO less cash capex')]:
  box=FancyBboxPatch((x,.65),.27,.13,transform=fig.transFigure,boxstyle='round,pad=0.012,rounding_size=0.01',facecolor='white',edgecolor=line,linewidth=.8,zorder=0)
  fig.add_artist(box);fig.text(x+.015,.746,label,fontsize=8,color=muted,fontweight='bold');fig.text(x+.015,.691,value,fontsize=26,color=ink,fontweight='bold');fig.text(x+.16,.699,note,fontsize=8,color=muted)
 ax=fig.add_axes([.065,.24,.55,.30],facecolor=bg);rows=h+f;positions=list(range(8))
 ax.axvspan(4.5,7.6,color='#e9f0e0',zorder=0);ax.axvline(4.5,color='#b7c7a8',linestyle=(0,(3,3)),lw=1)
 ax.bar(positions,[x['revenue']/1000 for x in rows],width=.48,color=[green]*5+[mint]*3,zorder=2)
 ax.plot(positions,[x['fcf']/1000 for x in rows],color=gold,lw=2.2,marker='o',markersize=4,zorder=3)
 for i,x in enumerate(rows):ax.text(i,x['revenue']/1000+12,f'{x["revenue"]/1000:.0f}',ha='center',color=muted,fontsize=9)
 ax.set_xticks(positions,[str(x['year'])+('F' if i>4 else 'A') for i,x in enumerate(rows)],fontsize=8,color=muted)
 ax.set_ylim(0,610);ax.set_xlim(-.6,7.6);ax.set_yticks([0,200,400,600],['0','200','400','600'],fontsize=8,color=muted);ax.grid(axis='y',color=line,lw=.7,zorder=1);ax.tick_params(length=0,pad=8)
 for spine in ax.spines.values():spine.set_visible(False)
 fig.text(.065,.59,'REVENUE & FREE CASH FLOW',fontweight='bold',fontsize=10,color=ink)
 fig.text(.065,.56,'USD billions · Base forecast shown in lighter bars',fontsize=9,color=muted)
 fig.text(.065,.185,'■ Revenue (actual)',fontsize=9,color=green);fig.text(.235,.185,'■ Revenue (forecast)',fontsize=9,color=muted);fig.text(.425,.185,'— Free cash flow',fontsize=9,color=gold)
 ax2=fig.add_axes([.735,.24,.21,.30],facecolor=bg)
 ss=['downside','base','upside'];values=[j['scenarios'][s][-1]['fcf']/1000 for s in ss]
 ax2.barh([2,1,0],values,color=['#c6ae88',green,'#8aab7e'],height=.47,zorder=2)
 for yy,value in zip([2,1,0],values):ax2.text(value+3,yy,f'${value:.1f}B',va='center',fontsize=10,color=ink)
 ax2.set_yticks([2,1,0],['Downside','Base','Upside'],fontsize=9,color=muted);ax2.set_xlim(0,170);ax2.set_ylim(-.6,2.6);ax2.set_xticks([]);ax2.tick_params(length=0,pad=8)
 for spine in ax2.spines.values():spine.set_visible(False)
 fig.text(.69,.59,'FY2029 SCENARIO OUTCOMES',fontweight='bold',fontsize=10,color=ink)
 fig.text(.69,.56,'Free cash flow · USD billions',fontsize=9,color=muted)
 fig.text(.69,.185,'Planning assumptions, not company guidance.',fontsize=8.5,color=muted)
 fig.text(.06,.11,'165 historical facts reconciled to original filings  /  48 core model checks passed',fontsize=10,color=green)
 fig.text(.06,.066,'Source: Microsoft SEC 10-K filings. Fiscal years end June 30. Snapshot: November 7, 2026.',fontsize=8,color=muted)
 fig.text(.06,.04,'Independent educational analysis. A = actual; F = forecast. Forecasts are conditional; not investment advice.',fontsize=8,color=muted)
 target=ROOT/'docs/images/financial_overview.png';fig.savefig(target,dpi=150,facecolor=bg);plt.close(fig);print(target)

if __name__=='__main__':main()
