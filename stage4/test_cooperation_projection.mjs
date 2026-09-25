import test from 'node:test';
import assert from 'node:assert/strict';
import {projection,beforeFire,alternatives,projectedFire,FIRE_END,planStory,timeOutcome,timeStory} from './cooperation-projection.mjs';
import {fineField} from './community_cooperation/model.mjs';
import {referenceWorld,snapshot} from './memory-model.mjs';
import {chartBounds} from './cooperation-recap.mjs';

test('Unplanted removal cycles, while planted plots establish',()=>{
 const plan={ecology:'C',removal:'A',community:'B'};
 for(const year of [2.5,7.5])assert.equal(projection(plan,year).removalCover,0);
 for(const year of [0,5,10])assert.ok(projection(plan,year).removalCover>.8);
 for(let y=.1;y<=10;y+=.1)assert.ok(Math.abs(projection(plan,y).removalCover-projection(plan,y-.1).removalCover)<.06);
 assert.ok(fineField(plan,5,true)[25*60+15].fuel>fineField(plan,7.5,true)[25*60+15].fuel);
 assert.equal(projection(plan,10).repeatClearings,1);
 assert.equal(projection({...plan,removal:'C'},8).removalCover,0);
 assert.equal(projection({...plan,removal:'B'},8).removalCover,0);
 assert.equal(projection(plan,10).shadeHeight,12);
 assert.equal(projection(plan,10).coffeeHeight,2);
 assert.equal(projection({...plan,community:'A'},10).coffeeHeight,0);
});
test('Chart uses tight linear bounds without clipping any plan or the zero axes',()=>{
 const points=alternatives(),b=chartBounds(points);
 assert.ok(b.xmin>-10);
 for(const p of points){assert.ok(p.earnings>b.xmin&&p.earnings<b.xmax);assert.ok(p.healthChange>b.ymin&&p.healthChange<b.ymax);}
 assert.ok(b.xmin<0&&b.xmax>0&&b.ymin<0&&b.ymax>0);
 assert.ok((Math.min(...points.map(p=>p.earnings))-b.xmin)/(b.xmax-b.xmin)<.08);
});
test('Recap includes all compatible plans and excludes the grant from earnings',()=>{
 const plans=alternatives();assert.equal(plans.length,21);
 assert.ok(plans.every(({plan})=>plan.community==='A'||plan.community!==plan.ecology));
 for(const {plan}of plans)assert.equal(beforeFire(plan,0).balance-beforeFire(plan,0).earnings,4);
 // An internal nursery order is not booked as new group revenue.
 assert.equal(beforeFire({ecology:'A',removal:'A',community:'A'},0).earnings,3);
 assert.ok(beforeFire({ecology:'A',removal:'C',community:'B'},0).balance<0);
});
test('All plans ignite at C, and grazing burns once in the first season',()=>{
 const world=referenceWorld(),state=snapshot();
 for(const community of ['A','B','C']){
  const p={ecology:'A',removal:'B',community},f=projectedFire(p,10);
  assert.equal(f.ignition,27);
  assert.equal(projection(p,10).fireMinutes,community==='C'?FIRE_END:0);
 }
 const grazing={ecology:'A',removal:'B',community:'C'};
 assert.deepEqual(projectedFire(grazing,10).arrival,projectedFire(grazing,.5).arrival);
 const restored={ecology:'C',removal:'A',community:'A'};
 assert.ok(projectedFire(restored,0).burned>projectedFire(restored,10).burned);
 assert.deepEqual(referenceWorld(),world);assert.deepEqual(snapshot(),state);
});
test('Cooperation health and income benefits have a consistent ordering',()=>{
 const points=alternatives(),top=[...points].sort((a,b)=>b.healthChange-a.healthChange);
 assert.deepEqual(top[0].plan,{ecology:'A',removal:'A',community:'A'});
 assert.equal(top[0].healthChange,17);
 for(const p of top.slice(1,3)){assert.equal(p.plan.ecology,'C');assert.equal(p.plan.community,'B');}
 const rich=[...points].sort((a,b)=>b.earnings-a.earnings);
 assert.equal(rich[0].plan.removal,'A');assert.ok(rich[0].healthChange<top[0].healthChange);
 const allA=beforeFire({ecology:'A',removal:'A',community:'A'});
 assert.ok(allA.earnings>5);assert.equal(allA.support.localPurchases,4);
 assert.ok(planStory({ecology:'C',removal:'C',community:'B'}).join(' ').includes('not included in this graph'));
 assert.ok(planStory({ecology:'B',removal:'B',community:'A'}).join(' ').includes('no matching order'));
});
test('Time comparison pays for later coffee, waits for harvest and preserves state',()=>{
 const world=referenceWorld(),state=snapshot();
 assert.deepEqual(timeOutcome('sequence',2),timeOutcome('nursery',2));
 assert.ok(Math.abs(timeOutcome('nursery',3).earnings-timeOutcome('sequence',3).earnings-6)<1e-8);
 assert.ok(timeOutcome('sequence',5).earnings<timeOutcome('sequence',3).earnings);
 assert.ok(timeOutcome('sequence',10).earnings>timeOutcome('sequence',6).earnings);
 assert.ok(timeOutcome('sequence',10).healthChange>timeOutcome('coffee',10).healthChange);
 // Later investment is not an unconditional winner: keeping the nursery saves cash.
 assert.ok(timeOutcome('nursery',10).earnings>timeOutcome('sequence',10).earnings);
 assert.ok(timeStory('sequence',3).join(' ').includes('6 credits'));
 assert.deepEqual(referenceWorld(),world);assert.deepEqual(snapshot(),state);
});
