import test from 'node:test';
import assert from 'node:assert/strict';
import {succession,followupBudget,followupReview,followupCandidates,followupStudy} from './neglect-model.mjs';
import {planBudget} from './round-model.mjs';
import {buildStructure,structureSummary} from './structure-model.mjs';
const previous={removal:'C',ecology:'C',...planBudget('C','C')};
test('same six-month starting point; divergent growth is explicit and reversible',()=>{
 const cared=succession(.5,true),uncared=succession(.5,false);assert.equal(cared.alive,uncared.alive);assert.equal(cared.invasive,uncared.invasive);
 assert.equal(succession(10,true).alive,80);assert.equal(succession(10,false).alive,15);assert.equal(succession(10,false).lost,65);
 let alive=90,cover=.15;for(let year=.5;year<=10;year+=.5){const x=succession(year,false);assert(x.alive<=alive);assert(x.invasive>=cover);alive=x.alive;cover=x.invasive;}
 assert.deepEqual(succession(3,false),succession(3,false));
});
test('old patch is expensive low-return care; new sites earn more without silently funding care',()=>{
 assert.deepEqual(followupCandidates(previous).map(p=>p.key),['C','D','E']);
 const care=followupBudget(previous,'C'),newSite=followupBudget(previous,'D');assert(care.cost>newSite.cost);assert(care.returns<newSite.returns);assert(care.left<newSite.left);assert(care.left>=0);
 assert.throws(()=>followupBudget(previous,'A'));
 const cared=followupReview(previous,'C',10),neglect=followupReview(previous,'D',10);assert(cared.future.burned<neglect.future.burned);assert(neglect.forecast.lost>0);
 assert.equal(cared.future.ignition,neglect.future.ignition);assert.deepEqual(previous,{removal:'C',ecology:'C',...planBudget('C','C')});
});
test('the same succession changes structure geometry while the reference stays fixed',()=>{
 const source=[];for(let x=-28;x<30;x+=2)for(let z=-18;z<20;z+=2)for(let y=0;y<32;y+=2)source.push(x,y,z);
 const species=[{name:'Native tree',growthForm:'tree'},{name:'Invasive grass',growthForm:'grass'}],centre={x:0,z:0};
 const make=(year,care,reference=false)=>buildStructure(source,null,centre,followupStudy(previous,'C',succession(year,care)),species,{reference});
 const good=structureSummary(make(10,true)),bad=structureSummary(make(10,false)),young=structureSummary(make(3,false));
 assert(good.upper>bad.upper);assert(bad.kinds[4]>good.kinds[4]);assert(bad.kinds[4]>young.kinds[4]);assert.deepEqual(make(3,false,true).points,make(10,false,true).points);
});
