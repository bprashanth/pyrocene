import test from 'node:test';
import assert from 'node:assert/strict';
import {projection,beforeFire,alternatives,projectedFire,FIRE_END,planStory,timeOutcome,timeStory,fieldPlots,planHinges} from './cooperation-projection.mjs';
import {recapFire} from './play-briefing.mjs';
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
test('A new fire uses the projection year and returning invasive fuel',()=>{
 const p={ecology:'A',removal:'C',community:'A'};
 assert.ok(projectedFire(p,5).burned>projectedFire(p,2.5).burned+2);
 assert.ok(projectedFire(p,10).burned>projectedFire(p,7.5).burned+2);
 const grazing={...p,community:'C'};
 // Automatic Projection retains its first-season grazing fire.
 assert.deepEqual(projectedFire(grazing,10).arrival,projectedFire(grazing,.5).arrival);
 // Manual Fire instead tests today's fuel, even for a grazing plan.
 assert.ok(projectedFire(grazing,5,{atProjectionYear:true}).burned>projectedFire(grazing,2.5,{atProjectionYear:true}).burned+2);
 assert.notDeepEqual(projectedFire(grazing,2.5,{atProjectionYear:true}).arrival,projectedFire(grazing,2.5).arrival);
});
test('Community income tapers with nursery orders and rises after delayed coffee harvest',()=>{
 const world=referenceWorld(),state=snapshot();
 assert.deepEqual(timeOutcome('sequence',2),timeOutcome('nursery',2));
 assert.equal(timeOutcome('sequence',2).investment,2);
 assert.equal(timeOutcome('sequence',3).investment,8);
 assert.equal(timeOutcome('coffee',0).investment,6);
 assert.equal(timeOutcome('coffee',3).annualIncome,-.3);
 assert.ok(timeOutcome('coffee',3.1).annualIncome>-.3);
 assert.ok(Math.abs(timeOutcome('sequence',6).annualIncome-timeOutcome('nursery',6).annualIncome+.3)<1e-8);
 assert.ok(timeOutcome('sequence',5).annualIncome<timeOutcome('sequence',3).annualIncome);
 assert.ok(timeOutcome('sequence',10).annualIncome>timeOutcome('sequence',6).annualIncome);
 assert.ok(timeOutcome('sequence',10).healthChange>timeOutcome('coffee',10).healthChange);
 assert.ok(timeOutcome('sequence',10).annualIncome>timeOutcome('nursery',10).annualIncome);
 assert.equal(timeOutcome('nursery',0).annualIncome,6);
 for(let y=.1;y<=10;y+=.1){assert.ok(timeOutcome('nursery',y).annualIncome>0);assert.ok(timeOutcome('nursery',y).annualIncome<timeOutcome('nursery',y-.1).annualIncome);}
 // No implication that annual community income is net group earnings.
 assert.equal(timeOutcome('sequence',10).earnings,undefined);
 assert.ok(timeStory('sequence',3).join(' ').includes('6 credits'));
 assert.deepEqual(referenceWorld(),world);assert.deepEqual(snapshot(),state);
});
test('Spatial comparison counts field plots without inventing a labour cost',()=>{
 assert.deepEqual(fieldPlots({ecology:'A',removal:'A',community:'A'}),['A']);
 assert.deepEqual(fieldPlots({ecology:'C',removal:'C',community:'B'}),['B','C']);
 assert.deepEqual(fieldPlots({ecology:'A',removal:'B',community:'C'}),['A','B','C']);
 for(const {plan}of alternatives())for(const year of [0,5,10]){const p=beforeFire(plan,year);assert.ok(Number.isFinite(p.earnings)&&Number.isFinite(p.healthChange));}
});
test('Hinge explanation matches the actual re-clearance payment and native loss',()=>{
 const plan={ecology:'A',removal:'B',community:'A'},events=planHinges(plan);
 assert.deepEqual(events.map(e=>e.year),[2,4,7.5]);
 const before=beforeFire(plan,7.499999),after=beforeFire(plan,7.5);
 assert.ok(after.earnings>before.earnings);assert.ok(after.health<before.health);
 assert.ok(events[2].text.includes((after.earnings-before.earnings).toFixed(1)+' credits'));
 assert.ok(events[2].text.includes((before.health-after.health).toFixed(1)+' native-health'));
 for(const {plan}of alternatives()){assert.equal(planHinges(plan).length,3);assert.equal(planHinges(plan)[2].year,projection(plan,10).repeatClearings?7.5:10);}
});
test('Closing recap uses the current Players fire scar without changing the world',()=>{
 const world=referenceWorld(),state=snapshot();assert.deepEqual(recapFire().arrival,projectedFire(null,0).arrival);
 assert.deepEqual(referenceWorld(),world);assert.deepEqual(snapshot(),state);
});
