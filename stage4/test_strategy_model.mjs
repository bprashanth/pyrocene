import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import { WORLD } from './world.mjs';
import { newGame, act, clone, ledger, metrics, observe, quote, replay, studyPlot, WORKABLE_IDS, CONFIG, forestHealth, fireTransmission, spreadFire } from './strategy-model.mjs';

test('player CLI distinguishes young planting from the completed canopy goal',()=>{
 const cli=fileURLToPath(new URL('./strategy-play.mjs',import.meta.url));
 const output=execFileSync(process.execPath,[cli,'113','remove:C2','restore:C2'],{encoding:'utf8'});
 assert.match(output,/YOUR MOVE 2\/24 turns/);
 assert.match(output,/GOAL 0\/3 restored canopies/);
 assert.doesNotMatch(output,/FINAL|19 closed canopies/);
 assert.equal(output.split('\n').filter(line=>line.startsWith('REMOVE C2:')).length,0);
});

test('strategy starts from actual WORLD ids and keeps intact forest in the state', () => {
  const g = newGame(17);
  assert.deepEqual(Object.keys(g.plots).map(Number), WORLD.filter(p => p.active).map(p => p.id));
  assert.equal(g.plots[13].coordinate, 'C2');
  assert.equal(g.plots[13].state, 'invaded');
  assert.equal(g.plots[0].state, 'closed');
  assert.ok(WORKABLE_IDS.length >= 8 - 1 && WORKABLE_IDS.length <= 12);
  assert.ok(metrics(g).health > 0 && metrics(g).health <= 100);
});

test('REMOVE opens a commitment, RESTORE creates young canopy, and care is explicit', () => {
  const g = newGame(113);
  const before = clone(g);
  const q = quote(g, 'remove', 'C2');
  assert.equal(q.valid, true);
  const removed = act(g, 'remove', 'C2');
  assert.ok(removed.some(e => e.type === 'work' && e.verb === 'remove'));
  assert.equal(g.plots[13].state, 'cleared');
  assert.equal(ledger(g).length, 1);
  assert.equal(g.credits, before.credits - q.cost + q.returns);
  const restored = act(g, 'restore', 13);
  assert.ok(restored.some(e => e.type === 'work' && e.verb === 'restore'));
  assert.equal(g.plots[13].state, 'young');
  assert.equal(g.plots[13].native, true);
  const cared = act(g, 'remove', 13);
  assert.ok(cared.some(e => e.care));
  assert.equal(g.plots[13].grass, g.plots[13].weeds);
  assert.equal(cared.find(e => e.care).returns, 0);
});

test('an open ledger closes with distinct canopy or reinvasion histories', () => {
  const failed = newGame(113);
  act(failed, 'remove', 13);
  for (let i = 0; i < 20 && failed.status === 'playing' && ledger(failed).length; i++) act(failed, 'wait');
  assert.equal(ledger(failed).length, 0);
  assert.equal(failed.ledgerHistory.at(-1).outcome, 'reinvaded');
  const held = newGame(113);
  act(held, 'remove', 13); act(held, 'restore', 13);
  for (let i = 0; i < 8 && ledger(held).length && held.status === 'playing'; i++) act(held, 'remove', 13);
  assert.equal(ledger(held).length, 0);
  assert.equal(held.ledgerHistory.at(-1).outcome, 'canopy');
  assert.ok(metrics(held).closedCanopy > 19);
});

test('commitment cap blocks new clearings but never blocks tending existing young plots', () => {
  const g = newGame(771);
  for (const id of WORKABLE_IDS.slice(0, CONFIG.commitmentCap)) act(g, 'remove', id);
  assert.equal(ledger(g).length, CONFIG.commitmentCap);
  const sixth = WORKABLE_IDS[CONFIG.commitmentCap];
  assert.equal(quote(g, 'remove', sixth).valid, false);
  const open = ledger(g)[0].id;
  act(g, 'restore', open);
  assert.equal(ledger(g).length, CONFIG.commitmentCap);
  assert.equal(quote(g, 'remove', open).valid, true);
});

test('observation, inspection, clone, and replay do not reroll deterministic ecology', () => {
  const moves = ['remove:C2', 'restore:C2', 'remove:C2', 'wait', 'wait'];
  const a = replay(41, moves);
  const snapshot = clone(a);
  observe(a); observe(a); studyPlot(a, 'C2');
  assert.deepEqual(a, snapshot);
  assert.deepEqual(replay(41, moves), a);
  assert.notDeepEqual(replay(42, moves), a);
});

test('fire event exposes origins, burned ids, arrival steps, paths, and plain reasons', () => {
  let found = null;
  for (let seed = 1; seed < 50 && !found; seed++) {
    const g = newGame(seed);
    for (let turn = 0; turn < 5 && !found; turn++) found = act(g, 'wait').find(e => e.type === 'fire');
  }
  assert.ok(found);
  assert.ok(Array.isArray(found.origins));
  assert.ok(Array.isArray(found.burned));
  assert.equal(typeof found.arrival, 'object');
  for (const origin of found.origins) assert.equal(found.arrival[origin], 0);
  for (const origin of found.origins) assert.ok(found.burned.includes(origin));
  assert.equal(typeof found.damage, 'object');
  assert.match(found.reason, /fuel|weather|canopy/i);
  assert.ok(Array.isArray(found.paths));
  assert.match(found.text, /fire/i);
  assert.ok(found.healthAfter < found.healthBefore);
  for(const id of found.burned) assert.ok(found.coverage[id]>0 && found.coverage[id]<=1);
});

function corridor(seed, canopy=0, closed=false) {
  const g=newGame(seed);
  // C1 -> C2 -> C3; every other plot is a restored closed-canopy barrier.
  for(const p of Object.values(g.plots)) Object.assign(p,{state:'closed',canopy:1,clearings:1,grass:.015,invasive:false});
  for(const id of [12,13,14]) Object.assign(g.plots[id],{state:'invaded',canopy:0,grass:1,invasive:true});
  if(canopy || closed) Object.assign(g.plots[13],{state:closed?'closed':'young',canopy,grass:.4,invasive:false});
  return g;
}

test('connected fuel burns farther; growing canopy reduces penetration and closed canopy blocks it',()=>{
  const totals=[0,0,0], downstream=[0,0,0];
  for(let seed=1;seed<=100;seed++) {
    for(const [i,canopy] of [0,.5,.9].entries()) {
      const g=corridor(seed,canopy),e=spreadFire(g,[12]);
      totals[i]+=e.coverage[13]||0; downstream[i]+=e.burned.includes(14)?1:0;
      assert.ok(e.healthAfter<e.healthBefore);
      for(const [from,to] of e.paths)assert.ok(e.burned.includes(from)&&e.burned.includes(to));
    }
    const g=corridor(seed,1,true),e=spreadFire(g,[12]);
    assert.deepEqual(e.burned,[12]);
    assert.equal(fireTransmission(g.plots[13]),0);
  }
  assert.ok(totals[0]>totals[1] && totals[1]>totals[2]);
  assert.ok(downstream[0]>downstream[1] && downstream[1]>=downstream[2]);
  assert.ok(downstream[0]>40,`Dense fuel should carry fire across the corridor: ${downstream}`);
});

test('dense invasion may scorch original forest edges without transmitting through them',()=>{
  let scorched=0;
  for(let seed=1;seed<=30;seed++) {
    const g=corridor(seed,1,true);
    g.plots[13].clearings=0;
    const e=spreadFire(g,[12]);
    if(!e.burned.includes(13))continue;
    scorched++;
    assert.ok(e.coverage[13]<=.22);
    assert.ok(g.plots[13].canopy<1 && g.plots[13].canopy>.8);
    assert.ok(!e.burned.includes(14));
    assert.ok(!e.paths.some(([from])=>from===13));
    assert.ok(forestHealth(g)<e.healthBefore);
  }
  assert.ok(scorched>0);
});

test('closed-forest fire damage persists as a canopy scar while shelter recovers', () => {
  const g = newGame(1);
  let damaged = null;
  for (let i = 0; i < 8 && !damaged; i++) {
    const events = act(g, 'wait');
    damaged = events.find(e => e.type === 'fireDamage' && g.plots[e.plot].state === 'closed');
  }
  assert.ok(damaged);
  const plot = g.plots[damaged.plot];
  assert.ok(plot.canopy < 1);
  const scar = plot.canopy;
  act(g, 'wait');
  assert.ok(g.plots[damaged.plot].canopy >= scar);
});

test('foundation is independent and accepts coordinate ids', () => {
  const foundation = { restored: 'C2', cleared: 'D5', cared: true, credits: 20 };
  const g = newGame(9, foundation);
  assert.equal(g.credits, 20);
  assert.equal(g.plots[13].state, 'young');
  assert.equal(g.plots[22].state, 'cleared');
  const h = newGame(9);
  assert.equal(h.plots[13].state, 'invaded');
  assert.equal(h.plots[22].state, 'invaded');
  assert.equal(studyPlot(g, 'D5').moisture, WORLD[22].moisture);
});

test('foundation care flag and prior clearance preserve different starting conditions', () => {
  const cared = newGame(9, { restored: 'C2', cared: true, credits: 10 });
  const uncared = newGame(9, { restored: 'C2', cared: false, credits: 10 });
  assert.ok(cared.plots[13].canopy > uncared.plots[13].canopy);
  assert.ok(cared.plots[13].grass < uncared.plots[13].grass);
  const legacy = newGame(9, { restored: 'C2', previousCleared: 'D5', cared: true });
  assert.equal(legacy.plots[22].state, 'cleared');
  assert.equal(ledger(legacy).length, 2);
});

test('studyPlot exposes active succession and canopy-conditioned field conditions', () => {
  const g = newGame(13);
  act(g, 'remove', 'C2'); act(g, 'restore', 'C2');
  const p = studyPlot(g, 'C2');
  assert.equal(p.active, true);
  assert.equal(p.succession.kind, 'young');
  assert.equal(p.succession.year, 1);
  assert.equal(p.succession.nativeFraction, p.canopy);
  assert.equal(p.succession.invasive, p.grass);
  assert.equal(p.moisture, p.succession.moisture);
  assert.equal(p.exposure, p.succession.exposure);
});

test('same-turn ledger closure does not reroll the current removal plot', () => {
  const g = newGame(7);
  act(g, 'remove', 13);
  g.plots[13].state = 'cleared';
  g.plots[13].grass = 0.87;
  g.commitments[0].state = 'open';
  act(g, 'remove', 28);
  assert.equal(g.plots[13].state, 'invaded');
  assert.equal(g.plots[28].grass, 0.035);
});
