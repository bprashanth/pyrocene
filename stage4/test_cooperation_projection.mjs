import test from 'node:test';
import assert from 'node:assert/strict';
import {projection,beforeFire,alternatives,projectedFire,FIRE_END} from './cooperation-projection.mjs';
import {fineField} from './community_cooperation/model.mjs';
import {referenceWorld,snapshot} from './memory-model.mjs';

test('Unplanted removal cycles, while planted plots establish',()=>{
 const plan={ecology:'C',removal:'A',community:'B'};
 for(const year of [0,3,6,9])assert.equal(projection(plan,year).removalCover,0);
 for(const year of [2,5,8])assert.ok(projection(plan,year).removalCover>.7);
 assert.ok(fineField(plan,2,true)[25*60+15].fuel>fineField(plan,3,true)[25*60+15].fuel);
 assert.equal(projection({...plan,removal:'C'},8).removalCover,0);
 assert.equal(projection({...plan,removal:'B'},8).removalCover,0);
 assert.equal(projection(plan,10).shadeHeight,12);
 assert.equal(projection(plan,10).coffeeHeight,2);
 assert.equal(projection({...plan,community:'A'},10).coffeeHeight,0);
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
