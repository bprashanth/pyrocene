import test from 'node:test';
import assert from 'node:assert/strict';
import {fire,INVENTORY,fineField,outcome,shadeSupport} from './model.mjs';
import {referenceWorld} from '../memory-model.mjs';
import {INVASIVE_IDS} from '../forest-flora.mjs';

test('Intact flanks have no invasives in inventory or fine field',()=>{
 for(const id of [26,28])assert.equal(INVENTORY[id].speciesIds.some(s=>INVASIVE_IDS.has(s)),false);
 fineField().forEach((c,i)=>{if([26,28].includes(Math.floor(i/600)*6+Math.floor(i%60/10)))assert.ok(c.invasion<=.1);});
});
test('Small ignition grows gradually and restoration interrupts the connection',()=>{
 const before=referenceWorld(),plan={ecology:'C',removal:'A',community:'B'},base=fire(null,10,'B'),future=fire(plan,10);
 assert.ok(base.burned>future.burned*2);
 assert.equal(base.arrival.filter(t=>t===0).length,1);
 assert.ok(base.arrival.filter(t=>Number.isFinite(t)&&t<=2).length<base.arrival.filter(Number.isFinite).length/3);
 assert.deepEqual(referenceWorld(),before);
 assert.deepEqual(fire(plan,10),future);
});
test('Recovery age affects fire, not just the picture',()=>{
 const p={ecology:'C',removal:'A',community:'B'};
 assert.ok(fire(p,0).burned>fire(p,10).burned);
});
test('Nursery requires an order and shade requires time and shelter',()=>{
 assert.match(outcome({ecology:'B',removal:'A',community:'A'}).livelihood,/No order/);
 assert.match(outcome({ecology:'A',removal:'A',community:'A'}).livelihood,/buyer/);
 const sheltered={ecology:'C',removal:'A',community:'B'},exposed={ecology:'A',removal:'C',community:'B'};
 assert.ok(shadeSupport(sheltered)>shadeSupport(exposed));
 assert.match(outcome(sheltered,0).livelihood,/not started/);
 assert.match(outcome(sheltered,10).livelihood,/improve/);
 assert.equal(outcome(sheltered).left,1);
});
