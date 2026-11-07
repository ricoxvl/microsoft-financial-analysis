import assert from 'node:assert/strict';
import fs from 'node:fs';
import {forecast,scenarioDrivers} from '../dashboards/web/model.js';
const data=JSON.parse(fs.readFileSync(new URL('../data/processed/model.json',import.meta.url)));
let comparisons=0;
for(const scenario of ['base','upside','downside']){
 const rows=forecast(data.history.at(-1),scenarioDrivers(data.drivers,scenario));
 rows.forEach((row,index)=>{
  const expected=data.scenarios[scenario][index];
  for(const [key,value] of Object.entries(row)){
   if(typeof value==='number'){assert.ok(Math.abs(value-expected[key])<.000001,`${scenario} ${row.year} ${key}`);comparisons++;}
  }
 });
}
for(const capex of [.15,.5])for(const margin of [.25,.6]){
 const rows=forecast(data.history.at(-1),{...data.drivers,capex_rate:capex,margin,dso:130});
 for(const r of rows){assert.ok(Math.abs(r.balance_check)<.01);assert.ok(Math.abs(r.cashflow_check)<.01);assert.ok(r.cash>=data.drivers.cash_floor-.01)}
}
console.log(`PASS: ${comparisons} browser/Python value comparisons and 12 stressed forecast years`);
