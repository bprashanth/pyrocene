import test from 'node:test';
import assert from 'node:assert/strict';
import {fire,INVENTORY,fineField,outcome,shadeSupport} from './model.mjs';
import {referenceWorld} from '../memory-model.mjs';
import {INVASIVE_IDS} from '../forest-flora.mjs';

test('Intact flanks have no invasive plants and lower surveyed fuel',()=>{
 for(const id of [26,28])assert.equal(INVENTORY[id].speciesIds.some(s=>INVASIVE_IDS.has(s)),false);
 for(const id of [26,28])assert.ok(INVENTORY[id].fuel<INVENTORY[27].fuel/2);
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
test('Fuel crosses survey borders smoothly and fire spills a little sideways',()=>{
 const field=fineField(),a=field[45*60+39],b=field[45*60+40];
 assert.ok(Math.abs(a.fuel-b.fuel)<.1);
 assert.ok(Math.abs(a.moisture-b.moisture)<.1);
 const arrival=fire(null,10,'C').arrival;
 const burnedIn=id=>arrival.filter((t,i)=>Number.isFinite(t)&&Math.floor(i/600)*6+Math.floor(i%60/10)===id).length;
 for(const id of [26,28]){assert.ok(burnedIn(id)>0);assert.ok(burnedIn(id)<25);}
 assert.ok(burnedIn(21)>burnedIn(26)*3);
 const forward=arrival.filter((t,i)=>Number.isFinite(t)&&Math.floor(i/60)<40).length;
 const backward=arrival.filter((t,i)=>Number.isFinite(t)&&Math.floor(i/60)>50).length;
 assert.ok(forward>backward*4);
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
