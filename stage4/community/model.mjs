/*
 * Community: an isolated buffer-agroforestry teaching experiment.
 *
 * The underlying fire and restoration rules come from strategy-model.mjs.
 * The additions here are deliberately small and are scenario mechanics, not
 * calibrated claims: two degraded edge plots can host one locally financed
 * agroforestry enterprise, and a simulated boundary source creates repeatable
 * fire pressure. Agroforestry lowers connected grass fuel as it is tended; it
 * is neither fireproof nor counted as native-forest restoration.
 */
import {
  VERSION as STRATEGY_VERSION,
  CONFIG as STRATEGY_CONFIG,
  WORLD,
  GRID,
  CELL,
  ACTION_MONTHS,
  PLOT_AREA_M2,
  WORKABLE_IDS,
  childOf,
  coordinate,
  centre,
  noise,
  weather,
  newGame as strategyNewGame,
  act as strategyAct,
  quote as strategyQuote,
  ledger as strategyLedger,
  metrics as strategyMetrics,
  observe as strategyObserve,
  studyPlot as strategyStudyPlot,
  spreadFire as strategySpreadFire,
  forestHealth,
  plotHealth,
  fireTransmission as strategyFireTransmission,
} from '../strategy-model.mjs';
import { INVASIVE_IDS } from '../forest-flora.mjs';

export { WORLD, GRID, CELL, ACTION_MONTHS, PLOT_AREA_M2, WORKABLE_IDS, childOf, coordinate, centre, noise, weather, forestHealth, plotHealth };

export const VERSION = 'community-1';

// Two short east-facing transects: boundary fuel -> buffer -> young native
// restoration -> standing forest. IDs remain ordinary 12x12 WORLD IDs.
export const SCENARIO = Object.freeze({
  bufferIds: Object.freeze([56, 68]),       // E9, F9
  restorationIds: Object.freeze([55, 67]), // E8, F8
  ignitionIds: Object.freeze([57, 69]),    // E10, F10 (outer boundary)
  forestIds: Object.freeze([54, 66]),      // E7, F7 (forest-side shelter)
});

export const ENTERPRISES = Object.freeze({
  nursery: Object.freeze({
    id: 'nursery',
    label: 'Community seed nursery',
    incomeStart: 1,
    incomeBase: 1.35,
    upkeep: 1.15,
    growth: 0.075,
    canopyCap: 0.48,
    crop: 'locally raised tree seedlings',
  }),
  shade: Object.freeze({
    id: 'shade',
    label: 'Cupuacu under mixed shade',
    incomeStart: 3,
    incomeBase: 2.2,
    upkeep: 1.35,
    growth: 0.095,
    canopyCap: 0.62,
    crop: 'cupuaçu shade produce',
  }),
});

export const CONFIG = Object.freeze({
  ...STRATEGY_CONFIG,
  turns: 24,
  goal: 2,
  startingCredits: 18,
  partnerCost: 5,
  boundaryFireBase: 0.08,
});

const cloneValue = value => JSON.parse(JSON.stringify(value));
const clamp = (value, low = 0, high = 1) => Math.max(low, Math.min(high, value));
const round = value => Math.round(value * 1000) / 1000;
const asId = value => {
  if (typeof value === 'string') {
    const text = value.trim().toUpperCase();
    const found = WORLD.find(plot => plot.active && coordinate(plot.id) === text);
    if (found) return found.id;
    if (/^\d+$/.test(text)) value = Number(text);
  }
  return Number.isInteger(value) ? value : null;
};

const enterpriseFor = value => {
  const id = String(value || 'nursery').toLowerCase();
  if (!ENTERPRISES[id]) throw Error("Community enterprise must be 'nursery' or 'shade'.");
  return ENTERPRISES[id];
};

function openFixtureCommitment(g, id, openedBy) {
  const p = g.plots[id];
  g.commitments.push({
    id,
    coordinate: coordinate(id),
    plot: p.name,
    openedTurn: g.turn,
    openedBy,
    state: 'open',
  });
}

function closeBufferCommitment(g, id) {
  const entry = [...g.commitments].reverse().find(item => item.id === id && item.state === 'open');
  if (!entry) return;
  Object.assign(entry, {
    state: 'closed',
    closedTurn: g.turn,
    outcome: 'buffer',
    reason: 'A community agroforestry buffer replaced exposed grass fuel.',
  });
  g.commitments = g.commitments.filter(item => item !== entry);
  g.ledgerHistory.push(cloneValue(entry));
}

function initialCommunity() {
  return {
    active: false,
    enterprise: null,
    age: 0,
    earned: 0,
    upkeep: 0,
    reserve: 0,
    carePaid: 0,
    rebuildPaid: 0,
    missedCare: 0,
    lastIncome: 0,
    lastCare: 0,
    cycles: 0,
  };
}

function prepareFixture(g) {
  g.limit = CONFIG.turns;
  g.credits = CONFIG.startingCredits;
  g.commitments = [];
  g.ledgerHistory = [];

  for (const id of SCENARIO.ignitionIds) {
    const p = g.plots[id];
    Object.assign(p, {
      state: 'invaded', invasive: true, native: false,
      grass: 0.96, canopy: 0, clearings: 0, visited: true,
      speciesIds: [...new Set([...p.speciesIds, 'urochloa_brizantha', 'urochloa_decumbens'])],
      last: 'Dense simulated boundary grass can carry an escaped fire toward the forest edge.',
    });
  }
  for (const id of SCENARIO.bufferIds) {
    const p = g.plots[id];
    Object.assign(p, {
      state: 'cleared', invasive: false, native: false,
      grass: 0.24, canopy: 0, clearings: 1, visited: true,
      speciesIds: [...new Set([...p.speciesIds, 'urochloa_brizantha', 'urochloa_decumbens'])],
      community: initialCommunity(),
      last: 'A degraded edge gap is cleared. It can be restored or used for the selected community buffer experiment.',
    });
    openFixtureCommitment(g, id, 'scenario-clearing');
  }
  for (const id of SCENARIO.restorationIds) {
    const p = g.plots[id];
    Object.assign(p, {
      state: 'young', invasive: false, native: true,
      grass: 0.18, canopy: 0.32, clearings: 1, visited: true,
      speciesIds: [...new Set([...p.speciesIds, 'urochloa_brizantha', 'urochloa_decumbens'])],
      failedPlanting: false,
      last: 'Young native restoration behind the edge needs care and remains vulnerable to fire.',
    });
    openFixtureCommitment(g, id, 'scenario-restoration');
  }
  for (const id of SCENARIO.forestIds) {
    const p = g.plots[id];
    Object.assign(p, {
      state: 'closed', invasive: false, native: true,
      grass: 0.025, canopy: 1, clearings: 0,
      speciesIds: p.speciesIds.filter(species => !INVASIVE_IDS.has(species)),
      last: 'Standing native forest lies behind the experimental edge plots.',
    });
  }
  for (const p of Object.values(g.plots)) p.weeds = p.grass;
}

export function newGame(seed = 113, options = {}) {
  const enterprise = enterpriseFor(options?.enterprise);
  const g = strategyNewGame(seed, null);
  prepareFixture(g);
  g.version = VERSION;
  g.enterprise = enterprise.id;
  g.communityNote = 'Simulated teaching parameters: agroforestry reduces grass fuel but is not a fireproof barrier or native restoration.';
  return g;
}

export function clone(g) { return cloneValue(g); }

function communityQuote(g, id) {
  const p = id == null ? null : g.plots[id];
  if (!p) return { valid: false, verb: 'partner', id, cost: 0, returns: 0, reason: 'Choose an active WORLD plot.' };
  if (!SCENARIO.bufferIds.includes(id)) return { valid: false, verb: 'partner', id, cost: CONFIG.partnerCost, returns: 0, productive: false, reason: 'This experiment can partner only on one of the two marked edge-buffer plots.' };
  if (p.state !== 'cleared' || p.community?.active) return { valid: false, verb: 'partner', id, cost: CONFIG.partnerCost, returns: 0, productive: false, reason: 'PARTNER needs a cleared, inactive buffer plot.' };
  const localContribution = p.community?.cycles
    ? round(Math.min(p.community.reserve, CONFIG.partnerCost))
    : 0;
  const cost = round(CONFIG.partnerCost - localContribution);
  const valid = g.credits >= cost;
  return { valid, verb: 'partner', id, cost, localContribution, returns: 0, productive: true, reason: valid ? null : `Rebuilding needs ${cost} project credits after ${localContribution} from the local reserve.` };
}

export function quote(g, verb, id = null) {
  const normalized = String(verb || '').toLowerCase();
  const actual = asId(id);
  if (normalized === 'partner') return communityQuote(g, actual);
  if (actual != null && g.plots[actual]?.community?.active && normalized === 'remove') {
    const valid = g.credits >= CONFIG.weedCost;
    return { valid, verb: normalized, id: actual, cost: CONFIG.weedCost, returns: 0, productive: true, care: true, reason: valid ? null : 'Supplementary weeding needs one project credit.' };
  }
  return strategyQuote(g, normalized, actual);
}

function activatePartnership(g, id, events) {
  const p = g.plots[id];
  const prior = p.community || initialCommunity();
  const q = communityQuote(g, id);
  p.community = {
    ...prior,
    active: true,
    enterprise: g.enterprise,
    age: 0,
    reserve: round(prior.reserve - q.localContribution),
    rebuildPaid: round(prior.rebuildPaid + q.localContribution),
    lastIncome: 0,
    lastCare: 0,
    cycles: prior.cycles + 1,
  };
  p.state = 'agroforestry';
  p.native = false;
  p.invasive = false;
  p.canopy = 0.1;
  p.grass = Math.min(p.grass, 0.16);
  p.failedPlanting = false;
  p.visited = true;
  p.receipt = { verb: 'partner', cost: q.cost, returns: 0, localContribution: q.localContribution };
  p.speciesIds = [...new Set([...(g.enterprise === 'shade' ? ['theobroma_grandiflorum'] : []), ...p.speciesIds])];
  p.last = `${ENTERPRISES[g.enterprise].label} planted as a mixed, non-native-restoration buffer.`;
  g.credits = round(g.credits - q.cost);
  events.push({
    type: 'community', verb: 'partner', plot: id, cost: q.cost, localContribution: q.localContribution,
    income: 0, care: 0, reserve: 0,
    text: q.localContribution
      ? `${p.name}: rebuilt the buffer with ${q.localContribution.toFixed(1)} local reserve and ${q.cost.toFixed(1)} project credits.`
      : `${p.name}: partnered on a ${g.enterprise === 'nursery' ? 'seed nursery' : 'cupuaçu shade plot'}; ${q.cost} project credits paid setup.`,
  });
}

function communitySeason(g, events) {
  const enterprise = ENTERPRISES[g.enterprise];
  for (const id of SCENARIO.bufferIds) {
    const p = g.plots[id];
    const c = p.community;
    if (!c?.active) continue;
    c.age += 1;
    const income = c.age >= enterprise.incomeStart
      ? round(enterprise.incomeBase * (0.86 + noise(g.seed, 'community-income', id, c.age) * 0.28))
      : 0;
    c.lastIncome = income;
    c.earned = round(c.earned + income);
    c.reserve = round(c.reserve + income);
    const due = enterprise.upkeep;
    const care = round(Math.min(c.reserve, due));
    c.lastCare = care;
    c.upkeep = round(c.upkeep + care);
    c.carePaid = round(c.carePaid + care);
    c.reserve = round(c.reserve - care);
    const careShare = due ? care / due : 1;
    if (careShare < 0.999) c.missedCare += 1;

    // Income is deliberately local: only this reserve can pay this tending.
    const growth = enterprise.growth * (0.3 + 0.7 * careShare) * (1 - p.burnScar * 0.45);
    p.canopy = round(clamp(p.canopy + growth, 0, enterprise.canopyCap));
    p.grass = round(clamp(p.grass * (0.82 - 0.34 * careShare) + 0.035 * (1 - p.canopy)));
    p.weeds = p.grass;
    p.last = careShare >= 0.999
      ? `Local ${enterprise.crop} income paid this season’s tending.`
      : `Local income covered only part of this season’s tending; grass pressure remains.`;
    const threshold = enterprise.canopyCap * 0.8;
    if (p.canopy >= threshold && g.commitments.some(item => item.id === id && item.state === 'open')) {
      closeBufferCommitment(g, id);
      events.push({
        type: 'community', plot: id, outcome: 'buffer', income: 0, care: 0, reserve: c.reserve,
        text: `${p.name}: mixed shade reached the scenario’s established-buffer threshold; native restoration is still tracked separately.`,
      });
    }
    events.push({
      type: 'community', plot: id, enterprise: g.enterprise,
      income, care, reserve: c.reserve,
      text: `${p.name}: local harvest ${income.toFixed(1)}; care ${care.toFixed(1)}; reserve ${c.reserve.toFixed(1)}.`,
    });
  }
}

function boundaryFire(g, events) {
  // Two setup seasons let the player place both marked buffers before the
  // recurring boundary-pressure experiment begins. Unrelated base fires can
  // still occur, so this is an opportunity, not an immunity period.
  if (g.turn <= 2) return null;
  const dryness = weather(g).dryness;
  const chance = CONFIG.boundaryFireBase + dryness * 0.12;
  if (noise(g.seed, 'community-boundary-fire', g.turn) >= chance) return null;
  const candidates = SCENARIO.ignitionIds.filter(id => g.plots[id]?.state !== 'closed');
  if (!candidates.length) return null;
  const origin = candidates[Math.floor(noise(g.seed, 'community-boundary-origin', g.turn) * candidates.length)];
  const event = strategySpreadFire(g, [origin], events);
  if (event) {
    event.simulatedBoundaryPressure = true;
    event.reason = 'A repeatable simulated boundary source tests connected fuel; it is not a forecast or a claim that agroforestry is fireproof.';
  }
  return event;
}

function applyCommunityFireDamage(g, records, events) {
  for (const id of SCENARIO.bufferIds) {
    const p = g.plots[id], c = p.community;
    if (!c?.active) continue;
    const hits = records.filter(record => record.burned.includes(id));
    if (!hits.length) continue;
    const intensity = clamp(hits.reduce((sum, record) => sum + (record.coverage[id] || 0), 0));
    const loss = round(Math.min(p.canopy, 0.07 + intensity * 0.42));
    p.canopy = round(Math.max(0, p.canopy - loss));
    p.grass = round(clamp(p.grass + 0.08 + intensity * 0.16));
    const failed = intensity > 0.48 && noise(g.seed, 'community-fire-loss', g.turn, id) < intensity * 0.62;
    if (failed) {
      c.active = false;
      c.lastIncome = 0;
      c.lastCare = 0;
      p.state = 'cleared';
      p.failedPlanting = true;
      p.canopy = 0;
      p.grass = Math.max(p.grass, 0.22);
      p.last = 'Fire destroyed the working buffer. A new partnership is needed to rebuild it.';
      if (!g.commitments.some(item => item.id === id && item.state === 'open')) openFixtureCommitment(g, id, 'fire-loss');
    } else {
      p.last = 'Fire crossed the buffer and reduced its shade; the local enterprise remains active.';
      if (p.canopy < ENTERPRISES[c.enterprise].canopyCap * 0.8 && !g.commitments.some(item => item.id === id && item.state === 'open')) openFixtureCommitment(g, id, 'fire-damage');
    }
    events.push({
      type: 'community', plot: id, fireDamage: loss, failed,
      income: 0, care: 0, reserve: c.reserve,
      text: failed
        ? `${p.name}: fire destroyed the buffer; PARTNER can rebuild it.`
        : `${p.name}: fire reduced buffer shade by ${Math.round(loss * 100)} points; it was not fireproof.`,
    });
  }
}

function finishEvents(g, events) {
  g.lastEvents = cloneValue(events);
  if (g.log.length) g.log[g.log.length - 1].events = cloneValue(events);
  // Base events are already journalled by strategyAct; add only Community ones.
  for (const event of events.filter(item => item.type === 'community')) {
    g.history.push({ turn: g.turn, ...cloneValue(event) });
  }
}

export function act(g, verb, id = null) {
  if (!g || g.version !== VERSION) throw Error('This is not a Community game state.');
  if (g.status !== 'playing') throw Error('This Community run is finished.');
  const normalized = String(verb || '').toLowerCase();
  const actual = asId(id);
  const q = quote(g, normalized, actual);
  if (!q.valid) throw Error(q.reason);

  const partnershipEvents = [];
  const manualBufferCare = normalized === 'remove' && actual != null && g.plots[actual]?.community?.active;
  if (normalized === 'partner') activatePartnership(g, actual, partnershipEvents);
  if (manualBufferCare) {
    const p = g.plots[actual];
    g.credits = round(g.credits - CONFIG.weedCost);
    p.grass = round(p.grass * 0.18);
    p.receipt = { verb: 'remove', cost: CONFIG.weedCost, returns: 0 };
    p.visited = true;
    partnershipEvents.push({
      type: 'work', verb: 'remove', plot: actual, cost: CONFIG.weedCost, returns: 0, care: true,
      text: `${p.name}: supplementary weeding protected the mixed crop; nothing was harvested or cleared.`,
    });
  }
  const recordsBefore = g.burnedRecords.length;
  g.version = STRATEGY_VERSION;
  let events;
  try {
    events = strategyAct(g, normalized === 'partner' || manualBufferCare ? 'wait' : normalized, normalized === 'partner' || manualBufferCare ? null : actual);
  } finally {
    g.version = VERSION;
  }
  if (normalized === 'partner' || manualBufferCare) {
    g.moves[g.moves.length - 1] = { verb: normalized, id: actual };
    const action = [...g.history].reverse().find(item => item.verb === 'wait' && item.turn === g.turn);
    if (action) Object.assign(action, { verb: normalized, plot: actual });
    events.unshift(...partnershipEvents);
  }

  communitySeason(g, events);
  boundaryFire(g, events);
  applyCommunityFireDamage(g, g.burnedRecords.slice(recordsBefore), events);
  for (const p of Object.values(g.plots)) p.weeds = p.grass;
  finishEvents(g, events);
  return events;
}

export function ledger(g) { return strategyLedger(g); }

export function metrics(g) {
  const base = strategyMetrics(g);
  const communities = SCENARIO.bufferIds.map(id => g.plots[id]?.community).filter(Boolean);
  const targetCanopies = SCENARIO.restorationIds.filter(id => g.plots[id]?.state === 'closed').length;
  return {
    ...base,
    partnerships: communities.filter(c => c.active).length,
    communityEarned: round(communities.reduce((sum, c) => sum + c.earned, 0)),
    communityCare: round(communities.reduce((sum, c) => sum + c.carePaid, 0)),
    communityReserve: round(communities.reduce((sum, c) => sum + c.reserve, 0)),
    targetCanopies,
    goal: CONFIG.goal,
  };
}

export function studyPlot(g, id) {
  const actual = asId(id);
  const detail = strategyStudyPlot(g, actual);
  const p = g.plots[actual];
  const eligible = SCENARIO.bufferIds.includes(actual) && p.state === 'cleared' && !p.community?.active;
  return {
    ...detail,
    succession: p.community?.active ? {
      ...detail.succession,
      kind: 'young',
      nativeFraction: 0,
      heightScale: round(0.13 + 0.87 * p.canopy),
      maintained: p.community.lastCare > 0,
      agroforestry: true,
    } : detail.succession,
    community: p.community ? cloneValue(p.community) : null,
    support: {
      eligible,
      recommended: SCENARIO.bufferIds.includes(actual),
      betweenIgnitionAndForest: SCENARIO.bufferIds.includes(actual),
      enterprise: g.enterprise,
      crop: ENTERPRISES[g.enterprise].crop,
      localOnly: true,
      note: p.community?.active
        ? 'Enterprise income enters this plot’s reserve and pays local care before any balance remains.'
        : eligible
          ? `PARTNER costs ${communityQuote(g, actual).cost} project credits after any local reserve contribution; later income stays with local care.`
          : 'This plot is outside the two marked buffer sites in this experiment.',
    },
    fieldNote: p.community?.active
      ? 'Mixed agroforestry lowers grass and fire transmission gradually. This managed buffer is not counted as restored native forest and can still burn.'
      : detail.fieldNote,
  };
}

export function inspect(g, id) {
  const actual = asId(id);
  if (actual == null || !g.plots[actual]) throw Error('Choose a plot.');
  g.plots[actual].inspected = true;
  return studyPlot(g, actual);
}

export function observe(g) {
  const base = strategyObserve(g);
  const m = metrics(g);
  return {
    ...base,
    version: VERSION,
    metrics: m,
    goal: `Close native canopy on both marked restoration plots (${m.targetCanopies}/${CONFIG.goal}); agroforestry shade does not count.`,
    note: `${g.communityNote} Each action advances six months; looking is free.`,
    plots: base.plots.map(item => {
      const p = g.plots[item.id];
      return p.community ? { ...item, community: cloneValue(p.community), support: studyPlot(g, item.id).support } : item;
    }),
  };
}

// Community plots are ordinary non-closed fuel plots to the base spread model;
// their gradually higher canopy/lower grass reduce, but never zero, transfer.
export function fireTransmission(p) {
  return strategyFireTransmission(p);
}

export function spreadFire(g, origins, events = []) {
  const before = g.burnedRecords.length;
  const event = strategySpreadFire(g, origins, events);
  if (event) applyCommunityFireDamage(g, g.burnedRecords.slice(before), events);
  return event;
}

function parseMove(move) {
  if (typeof move === 'string') {
    const [verb, id] = move.split(':');
    return { verb, id: id ?? null };
  }
  if (move && typeof move === 'object') return { verb: move.verb || move.action, id: move.id ?? move.plot ?? null };
  throw Error('Replay moves must be strings like partner:E9 or {verb,id}.');
}

export function replay(seed, moves = [], options = {}) {
  const g = newGame(seed, options);
  for (const move of moves) {
    if (g.status !== 'playing') break;
    const parsed = parseMove(move);
    act(g, parsed.verb, parsed.id);
  }
  return g;
}
