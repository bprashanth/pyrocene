import test from 'node:test';
import assert from 'node:assert/strict';
import {
  VERSION, CONFIG, SCENARIO, WORLD, GRID, CELL,
  newGame, act, clone, quote, ledger, metrics, studyPlot, replay,
  fireTransmission, spreadFire,
} from './model.mjs';

test('Community keeps Strategy geometry and starts the explicit edge fixture', () => {
  const g = newGame(17, { enterprise: 'nursery' });
  assert.equal(VERSION, 'community-1');
  assert.equal(GRID, 12);
  assert.equal(CELL, 75);
  assert.equal(WORLD.length, 144);
  assert.equal(g.credits, CONFIG.startingCredits);
  assert.equal(ledger(g).length, 4);
  for (const id of SCENARIO.bufferIds) {
    assert.equal(g.plots[id].state, 'cleared');
    assert.equal(g.plots[id].community.active, false);
    assert.equal(studyPlot(g, id).support.eligible, true);
  }
  for (const id of SCENARIO.restorationIds) assert.equal(g.plots[id].state, 'young');
  for (const id of SCENARIO.ignitionIds) assert.ok(g.plots[id].grass >= 0.9);
});

test('enterprise is one run-level choice and PARTNER is restricted to marked clearings', () => {
  assert.throws(() => newGame(1, { enterprise: 'both' }), /nursery.*shade/);
  const g = newGame(1, { enterprise: 'shade' });
  assert.equal(g.enterprise, 'shade');
  assert.equal(quote(g, 'partner', SCENARIO.bufferIds[0]).valid, true);
  assert.equal(quote(g, 'partner', SCENARIO.restorationIds[0]).valid, false);
  assert.equal(quote(g, 'partner', SCENARIO.ignitionIds[0]).valid, false);
});

test('local earnings pay local care and never become player credits', () => {
  const id = SCENARIO.bufferIds[0];
  const g = newGame(31, { enterprise: 'nursery' });
  const before = g.credits;
  const events = act(g, 'partner', id);
  const c = g.plots[id].community;
  assert.equal(g.credits, before - CONFIG.partnerCost);
  assert.ok(c.earned > 0);
  assert.ok(c.carePaid > 0);
  assert.ok(c.reserve >= 0);
  assert.equal(c.active, true);
  assert.ok(events.some(event => event.type === 'community' && /local harvest/.test(event.text)));
  const credits = g.credits;
  act(g, 'wait');
  assert.equal(g.credits, credits);
  assert.ok(g.plots[id].community.earned > c.lastIncome);
  assert.equal(quote(g, 'remove', id).valid, true);
  assert.equal(quote(g, 'remove', id).returns, 0);
});

test('agroforestry shade is not counted as native forest restoration', () => {
  const id = SCENARIO.bufferIds[0];
  const g = newGame(1, { enterprise: 'shade' });
  act(g, 'partner', id);
  for (let turn = 0; turn < 8; turn += 1) act(g, 'wait');
  assert.equal(g.plots[id].community.active, true);
  const p = g.plots[id];
  const m = metrics(g);
  assert.equal(p.state, 'agroforestry');
  assert.equal(p.native, false);
  assert.ok(p.canopy > 0.2 && p.canopy <= 0.62);
  assert.ok(p.speciesIds.includes('theobroma_grandiflorum'));
  assert.equal(m.restoredCanopies, SCENARIO.restorationIds.filter(plot => g.plots[plot].state === 'closed').length);
  assert.ok(studyPlot(g, id).fieldNote.includes('not counted as restored native forest'));
});

test('growing tended buffer lowers transmission but is not fireproof', () => {
  const id = SCENARIO.bufferIds[0];
  const g = newGame(1, { enterprise: 'shade' });
  const exposed = fireTransmission(g.plots[id]);
  act(g, 'partner', id);
  const young = fireTransmission(g.plots[id]);
  for (let turn = 0; turn < 7; turn += 1) act(g, 'wait');
  const tended = fireTransmission(g.plots[id]);
  assert.ok(exposed > young && young > tended);
  assert.ok(tended > 0);
});

test('forced fire can damage a buffer and destroyed buffers can be re-partnered', () => {
  let destroyed = null;
  for (let seed = 1; seed <= 100 && !destroyed; seed += 1) {
    const g = newGame(seed, { enterprise: 'nursery' });
    const id = SCENARIO.bufferIds[0];
    act(g, 'partner', id);
    g.plots[id].grass = 1;
    g.plots[id].canopy = 0.05;
    const events = [];
    spreadFire(g, [id], events);
    if (!g.plots[id].community.active) destroyed = { g, id, events };
  }
  assert.ok(destroyed, 'at least one deterministic seed destroys a severe directly ignited buffer');
  assert.equal(destroyed.g.plots[destroyed.id].state, 'cleared');
  const before = destroyed.g.plots[destroyed.id].community;
  const saved = before.reserve;
  const q = quote(destroyed.g, 'partner', destroyed.id);
  assert.equal(q.valid, true);
  assert.equal(q.localContribution, Math.min(saved, CONFIG.partnerCost));
  assert.equal(q.cost + q.localContribution, CONFIG.partnerCost);
  destroyed.g.credits = q.cost;
  act(destroyed.g, 'partner', destroyed.id);
  const rebuilt = destroyed.g.plots[destroyed.id].community;
  assert.equal(destroyed.g.credits, 0);
  assert.equal(rebuilt.active, true);
  assert.equal(rebuilt.cycles, 2);
  assert.equal(rebuilt.rebuildPaid, q.localContribution);
  assert.ok(Math.abs(rebuilt.earned - rebuilt.carePaid - rebuilt.reserve - rebuilt.rebuildPaid) < 0.01);
});

test('replay preserves enterprise, moves, local account and outcomes', () => {
  const moves = ['partner:E9', 'remove:E8', 'wait', 'remove:F8'];
  const direct = newGame(73, { enterprise: 'shade' });
  for (const move of moves) {
    const [verb, id] = move.split(':');
    act(direct, verb, id);
  }
  const played = replay(73, moves, { enterprise: 'shade' });
  assert.deepEqual(played, direct);
  assert.deepEqual(clone(played), played);
});

test('fire-damaged established buffers return to Unstable plots without duplicate entries', () => {
  const g = newGame(1, { enterprise: 'shade' }), id = SCENARIO.bufferIds[0];
  act(g, 'partner', id);
  const p = g.plots[id];
  p.canopy = 0.5;
  p.grass = 0.2;
  g.commitments.find(entry => entry.id === id && entry.state === 'open').state = 'buffer';
  spreadFire(g, [id], []);
  assert.equal(p.community.active, true);
  assert.ok(p.canopy < 0.62 * 0.8);
  assert.equal(ledger(g).filter(entry => entry.id === id).length, 1);
  spreadFire(g, [id], []);
  assert.equal(ledger(g).filter(entry => entry.id === id).length, 1);
});

function runPolicy(seed, enterprise, policy) {
  const g = newGame(seed, { enterprise });
  while (g.status === 'playing') {
    if (policy === 'buffer' && g.turn < SCENARIO.bufferIds.length) {
      act(g, 'partner', SCENARIO.bufferIds[g.turn]);
      continue;
    }
    if (policy !== 'neglect') {
      // Uses only the grass percentage shown to every player: tend when the
      // visible weed load reaches 30%, otherwise let a season pass.
      const target = SCENARIO.restorationIds.find(id => g.plots[id].state === 'young' && g.plots[id].grass >= 0.3 && quote(g, 'remove', id).valid);
      if (target != null) {
        act(g, 'remove', target);
        continue;
      }
    }
    act(g, 'wait');
  }
  const m = metrics(g);
  const vulnerableBurns = SCENARIO.restorationIds.filter(id => g.plots[id].burned > 0).length;
  return { ...m, vulnerableBurns };
}

test('80-seed public policies show benefit without a guaranteed shield', () => {
  const totals = {};
  for (const enterprise of ['nursery', 'shade']) {
    for (const policy of ['neglect', 'restore', 'buffer']) {
      const rows = Array.from({ length: 80 }, (_, index) => runPolicy(index + 1, enterprise, policy));
      totals[`${enterprise}:${policy}`] = {
        targets: rows.reduce((sum, row) => sum + row.targetCanopies, 0),
        burns: rows.reduce((sum, row) => sum + row.vulnerableBurns, 0),
        fireRuns: rows.filter(row => row.fireEvents > 0).length,
      };
    }
  }
  assert.ok(totals['nursery:buffer'].burns < totals['nursery:restore'].burns);
  assert.ok(totals['shade:buffer'].burns < totals['shade:restore'].burns);
  assert.ok(totals['nursery:buffer'].burns > 0);
  assert.ok(totals['shade:buffer'].burns > 0);
  assert.ok(totals['nursery:buffer'].targets > totals['nursery:neglect'].targets);
  assert.ok(totals['shade:buffer'].targets > totals['shade:neglect'].targets);
  assert.ok(totals['nursery:buffer'].fireRuns > 50);
  assert.ok(totals['shade:buffer'].fireRuns > 50);
});
