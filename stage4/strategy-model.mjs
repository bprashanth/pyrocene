/*
 * Strategy: a small, single-player restoration experiment.
 *
 * This model deliberately owns no shared round/coop authority.  It uses the
 * declared WORLD geometry and observations as a starting landscape, while
 * all rates below are teaching parameters for a quick six-month action game.
 * Random-looking outcomes are counter based: an inspection, undo, or replay
 * never consumes a random stream or changes a future result.
 */
import { WORLD, coordinate } from './world.mjs';

export const VERSION = 'strategy-1';
export const ACTION_MONTHS = 6;
// WORLD is a 900 m / 6-column declared grid: each active sector is 150 m
// square. UI copy should prefer the count because this remains a teaching
// footprint, not a surveyed burned-area estimate.
export const PLOT_AREA_M2 = 22500;

export const CONFIG = Object.freeze({
  turns: 24,
  startingCredits: 12,
  commitmentCap: 5,
  removeCost: 1,
  restoreCost: 5,
  weedCost: 1,
  firstClearReturn: 5,
  repeatClearReturn: 2,
  initialSaplingCover: 0.12,
  closureCover: 1,
  growth: 0.18,
  grassLoss: 0.88,
  fireYoungVulnerability: 4,
  fireReinvadedVulnerability: 1.15,
});

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const round = x => Math.round(x * 1000) / 1000;
const cloneValue = x => JSON.parse(JSON.stringify(x));

// A stable integer hash.  Keep keys explicit so adding an observation does not
// perturb any action, weather, growth, or fire result.
export function noise(seed, ...keys) {
  let h = (Number(seed) || 113) >>> 0;
  for (const key of keys.join('|')) {
    h ^= key.charCodeAt(0);
    h = Math.imul(h, 16777619);
    h ^= h >>> 13;
  }
  h = Math.imul(h ^ (h >>> 16), 2246822507);
  return (h >>> 0) / 4294967296;
}

const byId = new Map(WORLD.map(plot => [plot.id, plot]));
const activeWorld = WORLD.filter(plot => plot.active);
const activeIds = new Set(activeWorld.map(plot => plot.id));
// These are the actual invasive patches in WORLD, including edge and deeper
// sites.  Intact neighbouring forest remains in the fire/invasion simulation.
export const WORKABLE_IDS = Object.freeze(activeWorld.filter(plot => plot.invasive).map(plot => plot.id));

const asId = value => {
  if (typeof value === 'string') {
    const text = value.trim().toUpperCase();
    const found = activeWorld.find(plot => coordinate(plot.id).toUpperCase() === text);
    if (found) return found.id;
    if (/^\d+$/.test(text)) value = Number(text);
  }
  if (Number.isInteger(value) && byId.has(value)) return value;
  return null;
};

const neighbourIds = id => {
  const row = Math.floor(id / 6), col = id % 6;
  const ids = [];
  for (let dr = -1; dr <= 1; dr += 1) for (let dc = -1; dc <= 1; dc += 1) {
    if (!dr && !dc) continue;
    const r = row + dr, c = col + dc;
    if (r < 0 || c < 0 || c >= 6) continue;
    const candidate = r * 6 + c;
    if (activeIds.has(candidate)) ids.push(candidate);
  }
  return ids;
};

// A closed plot can carry a fire scar and temporarily have less than 100%
// canopy. It remains a closed commitment outcome while recovering shelter.
const intactState = plot => plot.state === 'closed';
const growingState = plot => plot.state === 'young';
const fuelFor = plot => clamp(plot.fuel * (0.16 + 0.92 * plot.grass) * (plot.state === 'young' ? 0.72 : 1) * (plot.invasive && plot.clearings > 0 ? 1.3 : 1));
const effectiveMoisture = plot => clamp(plot.moisture + plot.canopy * 0.4);
const effectiveExposure = plot => clamp(plot.exposure - plot.canopy * 0.55);

function shelter(g, id) {
  const p = g.plots[id];
  if (!p) return 0;
  let value = 0;
  for (const n of neighbourIds(id)) {
    const q = g.plots[n];
    if (!q) continue;
    const native = q.native ? 1 : 0.4;
    const cover = intactState(q) ? q.canopy : q.state === 'young' ? q.canopy * 0.45 : 0;
    value += native * cover * (1 - q.nativeLoss * 0.35);
  }
  // A patch's own repeated mining also removes the sheltered seed source.
  return clamp(value / Math.max(1, neighbourIds(id).length) * (1 - p.nativeLoss * 0.25));
}

function nearestNative(g, id) {
  return neighbourIds(id).filter(n => g.plots[n] && g.plots[n].native && intactState(g.plots[n]));
}

export function weather(g, id = null) {
  const turn = g.turn;
  const global = noise(g.seed, 'weather', turn);
  const plotNoise = id == null ? 0.5 : noise(g.seed, 'weather-plot', turn, id);
  const p = id == null ? null : g.plots[id];
  const dryness = clamp(0.2 + global * 0.48 + plotNoise * 0.22 + (p ? effectiveExposure(p) * 0.18 : 0) - (p ? effectiveMoisture(p) * 0.28 : 0));
  return { turn, label: dryness > 0.68 ? 'dry' : dryness < 0.38 ? 'wet' : 'mixed', dryness: round(dryness), global: round(global) };
}

function plotWeather(g, id) {
  return weather(g, id);
}

function newPlot(source, seed = 113) {
  const invasive = !!source.invasive;
  const forest = !invasive;
  return {
    id: source.id,
    coordinate: coordinate(source.id),
    name: source.name || coordinate(source.id),
    state: forest ? 'closed' : 'invaded',
    invasive,
    native: !invasive,
    habitat: !!source.habitat,
    people: !!source.people,
    moisture: source.moisture,
    exposure: source.exposure,
    fuel: source.fuel,
    speciesIds: [...(source.speciesIds || [])],
    disturbance: source.disturbance || null,
    grass: invasive ? round(clamp(0.72 + 0.22 * noise(seed, 'initial-grass', source.id))) : round(clamp(0.06 + 0.08 * noise(seed, 'forest-litter', source.id))),
    canopy: forest ? 1 : 0,
    nativeLoss: 0,
    clearings: 0,
    burned: 0,
    last: forest ? 'Standing native forest shelters nearby recovery.' : 'Invasive fuel is available for removal.',
    history: [],
    weeds: 0,
  };
}

function syncPlotAliases(g) {
  for (const p of Object.values(g.plots)) p.weeds = p.grass;
}

function foundationIds(foundation) {
  const out = {};
  if (!foundation || typeof foundation !== 'object') return out;
  for (const key of ['restored', 'cleared', 'previousCleared']) {
    if (foundation[key] == null) continue;
    const id = asId(foundation[key]);
    if (id == null || !activeIds.has(id)) throw Error(`Foundation ${key} must identify an active WORLD plot.`);
    out[key] = id;
  }
  return out;
}

export function newGame(seed = 113, foundation = null) {
  const actualSeed = Number.isFinite(Number(seed)) ? Number(seed) : 113;
  const g = {
    version: VERSION,
    seed: actualSeed,
    turn: 0,
    limit: CONFIG.turns,
    seasonMonths: 0,
    credits: Number.isFinite(Number(foundation?.credits)) ? Number(foundation.credits) : CONFIG.startingCredits,
    status: 'playing',
    plots: Object.fromEntries(activeWorld.map(plot => [plot.id, newPlot(plot, actualSeed)])),
    commitments: [],
    ledgerHistory: [],
    history: [],
    log: [],
    moves: [],
    burned: [],
    burnedRecords: [],
    lastEvents: [],
    foundation: foundation ? cloneValue(foundation) : null,
  };
  const ids = foundationIds(foundation);
  const foundationCleared = [...new Set([ids.previousCleared, ids.cleared].filter(id => id != null))];
  for (const clearedId of foundationCleared) {
    const p = g.plots[clearedId];
    p.state = 'cleared'; p.invasive = false; p.native = true; p.grass = 0.06; p.canopy = 0; p.clearings = 1;
    openCommitment(g, p.id, 'foundation');
    p.last = 'Cleared ground from the starting foundation; restore before grass returns.';
  }
  if (ids.restored != null) {
    const p = g.plots[ids.restored];
    const wasCleared = foundationCleared.includes(ids.restored);
    if (wasCleared) {
      p.state = 'young'; p.invasive = false; p.native = true; p.grass = foundation?.cared ? 0.04 : 0.4; p.canopy = foundation?.cared ? 0.2 : 0.1; p.clearings = Math.max(1, p.clearings);
      if (!g.commitments.some(c => c.id === p.id && c.state === 'open')) openCommitment(g, p.id, 'foundation');
      p.last = foundation?.cared ? 'Young trees from the foundation are being cared for.' : 'Young trees from the foundation need care.';
    } else {
      p.state = 'young'; p.invasive = false; p.native = true; p.grass = foundation?.cared ? 0.04 : 0.4; p.canopy = foundation?.cared ? 0.2 : 0.1; p.clearings = Math.max(1, p.clearings);
      openCommitment(g, p.id, 'foundation');
      p.last = foundation?.cared ? 'Young trees from the foundation are being cared for.' : 'Young trees from the foundation need care.';
    }
    p.foundationCared = !!foundation?.cared;
  }
  syncPlotAliases(g);
  return g;
}

function openCommitment(g, id, openedBy = 'remove') {
  const p = g.plots[id];
  const entry = { id, coordinate: coordinate(id), plot: p.name, openedTurn: g.turn, openedBy, state: 'open' };
  g.commitments.push(entry);
  return entry;
}

function closeCommitment(g, id, outcome, reason) {
  const entry = [...g.commitments].reverse().find(c => c.id === id && c.state === 'open');
  if (!entry) return null;
  entry.state = 'closed'; entry.closedTurn = g.turn; entry.outcome = outcome; entry.reason = reason;
  g.commitments = g.commitments.filter(c => c !== entry);
  g.ledgerHistory.push(cloneValue(entry));
  return entry;
}

export function clone(g) { return cloneValue(g); }

const jobFor = p => p?.state === 'invaded' ? 'remove' : p?.state === 'cleared' || p?.state === 'young' ? (p.state === 'cleared' ? 'restore' : 'remove') : null;

export function quote(g, verb, id = null) {
  const normalized = String(verb || '').toLowerCase();
  if (normalized === 'wait') return { valid: true, verb: 'wait', id: null, cost: 0, returns: 0, productive: false, reason: 'No productive job selected; this passes six months.' };
  const actual = asId(id);
  if (actual == null || !g.plots[actual]) return { valid: false, verb: normalized, id: actual, cost: 0, returns: 0, reason: 'Choose an active WORLD plot (for example C2).' };
  const p = g.plots[actual];
  if (!['remove', 'restore'].includes(normalized)) return { valid: false, verb: normalized, id: actual, cost: 0, returns: 0, reason: 'Strategy actions are REMOVE or RESTORE.' };
  if (normalized === 'remove' && p.state === 'invaded') {
    const open = g.commitments.filter(c => c.state === 'open').length;
    if (open >= CONFIG.commitmentCap) return { valid: false, verb: normalized, id: actual, cost: CONFIG.removeCost, returns: 0, reason: `Five open commitments already exist. Restore or wait for one to resolve.` };
    const returns = p.clearings ? CONFIG.repeatClearReturn : CONFIG.firstClearReturn + Math.round(noise(g.seed, 'return', actual) * 2);
    const affordable = g.credits - CONFIG.removeCost + returns >= 0;
    return { valid: affordable, verb: normalized, id: actual, cost: CONFIG.removeCost, returns, productive: true, reason: affordable ? null : 'Clearance needs more credits.' };
  }
  if (normalized === 'remove' && p.state === 'young') {
    return { valid: g.credits >= CONFIG.weedCost, verb: normalized, id: actual, cost: CONFIG.weedCost, returns: 0, productive: true, reason: g.credits >= CONFIG.weedCost ? null : 'Care needs one credit.' };
  }
  if (normalized === 'restore' && p.state === 'cleared') {
    return { valid: g.credits >= CONFIG.restoreCost, verb: normalized, id: actual, cost: CONFIG.restoreCost, returns: 0, productive: true, reason: g.credits >= CONFIG.restoreCost ? null : 'Restoration needs five credits.' };
  }
  return { valid: false, verb: normalized, id: actual, cost: 0, returns: 0, productive: false, reason: normalized === 'remove' ? 'REMOVE weeds only around young trees or clears invaded fuel.' : 'RESTORE only plants a cleared plot.' };
}

function addHistory(g, event) {
  g.history.push({ turn: g.turn, ...cloneValue(event) });
}

function work(g, verb, id, events) {
  const p = id == null ? null : g.plots[id];
  if (verb === 'remove' && p.state === 'invaded') {
    const q = quote(g, verb, id);
    g.credits += q.returns - q.cost;
    p.state = 'cleared'; p.invasive = false; p.native = p.native || false; p.grass = 0.035; p.canopy = 0; p.clearings += 1;
    if (p.clearings > 1) {
      p.nativeLoss = round(clamp(p.nativeLoss + 0.28));
      p.last = 'Repeated clearance earned less and removed some native shelter.';
      events.push({ type: 'nativeLoss', plot: id, text: `${p.name}: repeat mining reduced native shelter.` });
    } else p.last = 'Cleared ground. Restore before returning grass closes the window.';
    openCommitment(g, id);
    events.unshift({ type: 'work', verb, plot: id, cost: q.cost, returns: q.returns, text: `Removed invasive fuel at ${p.name}. Earned ${q.returns} after a ${q.cost}-credit clearance cost.` });
    return;
  }
  if (verb === 'restore' && p.state === 'cleared') {
    g.credits -= CONFIG.restoreCost;
    p.state = 'young'; p.invasive = false; p.native = true; p.grass = 0.035; p.canopy = CONFIG.initialSaplingCover;
    p.last = 'Young native trees planted. Grass removal is careful and costs one credit.';
    if (!g.commitments.some(c => c.id === id && c.state === 'open')) openCommitment(g, id, 'restore');
    events.unshift({ type: 'work', verb, plot: id, cost: CONFIG.restoreCost, returns: 0, text: `Restored ${p.name}. Young canopy now needs time and careful weeding.` });
    return;
  }
  if (verb === 'remove' && p.state === 'young') {
    g.credits -= CONFIG.weedCost;
    p.grass = round(clamp(p.grass * 0.18)); p.last = 'Careful weeds removed around the young trees. No clearance income.';
    events.unshift({ type: 'work', verb, plot: id, cost: CONFIG.weedCost, returns: 0, care: true, text: `Removed weeds carefully at ${p.name}. It costs ${CONFIG.weedCost} and earns no clearance return.` });
  }
}

function advanceEcology(g, actionId, events) {
  const prior = cloneValue(g.plots);
  for (const source of activeWorld) {
    const p = g.plots[source.id];
    const w = plotWeather(g, source.id);
    if (p.state === 'closed') {
      p.canopy = round(clamp(p.canopy + 0.025));
      // Standing native forest is shelter, not immunity: a dry fire can still burn it.
      p.grass = round(clamp(p.grass * 0.85 + 0.015));
      continue;
    }
    // Exposed openings can add roughly .16-.24 grass cover per six months;
    // neighbouring native canopy materially suppresses that return.
    const local = 0.055 + 0.075 * noise(g.seed, 'grass', g.turn, source.id);
    const sourceGrass = neighbourIds(source.id).reduce((sum, n) => sum + (prior[n]?.grass || 0) * (prior[n]?.invasive ? 1 : 0.35), 0);
    const neighbourPressure = sourceGrass / Math.max(1, neighbourIds(source.id).length);
    const shelterValue = shelter(g, source.id);
    const grassGrowth = (local + neighbourPressure * 0.15) * (0.9 + w.dryness * 0.7) * (1 - shelterValue * 0.55);
    // Use the action journal, not event history: resolving a different plot's
    // ledger earlier in this phase must not change the current removal plot's
    // deterministic no-regrowth turn.
    if (!(source.id === actionId && g.moves.at(-1)?.verb === 'remove')) p.grass = round(clamp(p.grass + grassGrowth));
    if (p.state === 'cleared' && p.grass >= CONFIG.grassLoss) {
      p.state = 'invaded'; p.invasive = true; p.canopy = 0; p.last = 'Returning grass reinvaded the cleared plot.';
      const closed = closeCommitment(g, source.id, 'reinvaded', 'Grass returned before canopy closure.');
      events.push({ type: 'reinvaded', plot: source.id, outcome: 'reinvaded', text: `${p.name}: returning grass closed the commitment without canopy.` });
      if (closed) addHistory(g, { type: 'ledgerClose', plot: source.id, outcome: 'reinvaded', text: `${p.name}: commitment ended when grass returned.` });
    }
    if (p.state === 'young' && p.grass >= CONFIG.grassLoss) {
      p.state = 'invaded'; p.invasive = true; p.native = false; p.canopy = 0; p.last = 'Returning grass overwhelmed the young planting.';
      const closed = closeCommitment(g, source.id, 'reinvaded', 'Grass overwhelmed the young planting.');
      events.push({ type: 'reinvaded', plot: source.id, outcome: 'reinvaded', text: `${p.name}: grass overwhelmed the young planting; the commitment ended without canopy.` });
      if (closed) addHistory(g, { type: 'ledgerClose', plot: source.id, outcome: 'reinvaded', text: `${p.name}: commitment ended when grass overwhelmed the planting.` });
      continue;
    }
    if (p.state === 'young') {
      const stress = 1 - w.dryness * 0.42;
      const competition = Math.max(0.2, 1 - p.grass * 0.82);
      const boost = 1 + shelterValue * 0.3;
      const growth = CONFIG.growth * stress * competition * boost * (0.92 + noise(g.seed, 'growth', g.turn, source.id) * 0.16);
      p.canopy = round(clamp(p.canopy + growth));
      p.last = p.grass > 0.55 ? 'Grass competition is slowing young canopy growth.' : w.dryness > 0.68 ? 'A dry season is slowing young canopy growth.' : shelterValue > 0.25 ? 'Young canopy is growing with nearby native shelter.' : 'Young canopy is growing; grass is still present.';
      events.push({ type: 'growth', plot: source.id, growth: round(growth), text: `${p.name}: ${p.last}` });
      if (p.canopy >= CONFIG.closureCover) {
        p.state = 'closed'; p.native = true; p.invasive = false; p.grass = 0.015; p.last = 'Canopy closed. The commitment left the ledger.';
        const closed = closeCommitment(g, source.id, 'canopy', 'Native canopy closed.');
        events.push({ type: 'closed', plot: source.id, outcome: 'canopy', text: `${p.name}: canopy closed and the commitment ended.` });
        if (closed) addHistory(g, { type: 'ledgerClose', plot: source.id, outcome: 'canopy', text: `${p.name}: commitment ended at canopy closure.` });
      }
    }
  }
}

function fire(g, events) {
  const weatherNow = weather(g);
  const origins = [];
  for (const source of activeWorld.filter(p => p.people && p.exposure >= 0.6)) {
    const state = g.plots[source.id];
    const fuel = fuelFor(state);
    // 33 is the declared ignition-side plot; other people-use edge plots are
    // smaller possibilities.  Reinvaded fuel raises risk rather than forcing it.
    const weight = source.id === 33 ? 1.55 : 0.45;
    const reinvaded = state.invasive && state.clearings > 0;
    const chance = clamp((0.012 + weatherNow.dryness * 0.12) * weight * (0.35 + fuel) * (state.invasive ? 1.28 : 1) * (reinvaded ? 1.35 : 1));
    if (noise(g.seed, 'ignite', g.turn, source.id) < chance) origins.push(source.id);
  }
  if (!origins.length) return null;
  const burned = new Set(origins);
  const arrival = Object.fromEntries(origins.map(id => [id, 0]));
  const damage = {};
  const paths = [];
  const queue = origins.map(id => ({ id, step: 0 }));
  const seen = new Set(origins);
  while (queue.length) {
    const current = queue.shift();
    for (const next of neighbourIds(current.id)) {
      if (seen.has(next)) continue;
      const p = g.plots[next];
      const localDryness = plotWeather(g, next).dryness;
      const shelterValue = shelter(g, next);
      const vulnerability = p.state === 'young' ? CONFIG.fireYoungVulnerability : p.invasive && p.clearings > 0 ? CONFIG.fireReinvadedVulnerability : 1;
      const chance = clamp((0.08 + fuelFor(p) * 0.47) * (0.4 + localDryness * 0.85) * (0.82 + effectiveExposure(p) * 0.35) * vulnerability * (1 - shelterValue * 0.28));
      if (noise(g.seed, 'spread', g.turn, current.id, next) < chance) {
        const step = current.step + 1;
        seen.add(next); queue.push({ id: next, step }); burned.add(next); arrival[next] = step; paths.push([current.id, next]);
      }
    }
  }
  for (const id of burned) {
    const p = g.plots[id];
    p.burned += 1;
    p.last = p.state === 'young' ? 'Fire burned the young trees and reduced canopy.' : p.state === 'closed' ? 'Fire burned standing forest; closure reduces but does not remove risk.' : 'Fire crossed this fuel patch.';
    if (p.state === 'young') {
      const loss = round(0.3 + plotWeather(g, id).dryness * 0.6);
      const applied = round(Math.min(p.canopy, loss));
      p.canopy = round(Math.max(0, p.canopy - applied));
      damage[id] = applied;
      events.push({ type: 'fireDamage', plot: id, damage: applied, reason: 'vulnerable saplings burned' , text: `${p.name}: fire damaged vulnerable saplings (${Math.round(applied * 100)} canopy points).` });
      if (p.canopy <= 0.02) { p.state = 'cleared'; p.invasive = false; p.grass = 0.12; }
    } else if (p.state === 'closed') {
      damage[id] = 0.1;
      p.canopy = round(Math.max(0.55, p.canopy - damage[id]));
      events.push({ type: 'fireDamage', plot: id, damage: 0.1, reason: 'standing canopy burned', text: `${p.name}: standing forest burned; closed canopy reduced but did not eliminate the risk.` });
    } else damage[id] = 0;
  }
  const fresh = [...burned].filter(id => !g.burned.includes(id));
  for (const id of fresh) g.burned.push(id);
  const record = { turn: g.turn, origins, burned: [...burned], arrival, paths };
  g.burnedRecords.push(record);
  const reinvadedOrigins = origins.filter(id => g.plots[id].invasive && g.plots[id].clearings > 0);
  const reason = reinvadedOrigins.length ? 'Dry weather and connected fuel allowed an ignition; reinvaded fuel raised the risk at ' + reinvadedOrigins.map(coordinate).join(', ') + '. Closed canopy reduced but did not remove spread.' : 'Dry weather and connected fuel allowed an ignition to spread; closed canopy reduced risk but did not make it zero.';
  const event = { type: 'fire', origins, burned: [...burned], arrival, paths, damage, reason, text: burned.size ? `Fire from ${origins.map(coordinate).join(', ')} reached ${burned.size} plot${burned.size === 1 ? '' : 's'} including its ignition plot.` : `Fire ignited at ${origins.map(coordinate).join(', ')} but did not cross into a neighbouring plot.` };
  events.push(event); return event;
}

export function act(g, verb, id = null) {
  if (!g || g.version !== VERSION) throw Error('This is not a Strategy game state.');
  if (g.status !== 'playing') throw Error('This Strategy run is finished.');
  const normalized = String(verb || '').toLowerCase();
  if (normalized === 'wait') {
    if (g.credits < 0) throw Error('No credits remain.');
  }
  const actual = asId(id);
  const q = quote(g, normalized, actual);
  if (!q.valid) throw Error(q.reason);
  const events = [];
  if (normalized !== 'wait') work(g, normalized, actual, events);
  g.turn += 1; g.seasonMonths += ACTION_MONTHS;
  g.moves.push({ verb: normalized, id: actual });
  g.history.push({ turn: g.turn, verb: normalized, plot: actual, months: ACTION_MONTHS });
  advanceEcology(g, actual, events);
  fire(g, events);
  syncPlotAliases(g);
  g.credits = round(g.credits);
  g.lastEvents = cloneValue(events);
  g.log.push({ turn: g.turn, events: cloneValue(events) });
  for (const event of events) addHistory(g, event);
  if (g.turn >= g.limit) g.status = 'done';
  g.status = g.status === 'playing' && g.credits < 0 ? 'broke' : g.status;
  return events;
}

export function ledger(g) {
  return g.commitments.filter(entry => entry.state === 'open').map(cloneValue);
}

export function metrics(g) {
  const allPlots = Object.values(g.plots);
  const closed = allPlots.filter(intactState).length;
  const restoredClosed = allPlots.filter(p => intactState(p) && p.clearings > 0).length;
  const young = allPlots.filter(p => p.state === 'young').length;
  const invaded = allPlots.filter(p => p.state === 'invaded').length;
  return {
    turn: g.turn,
    months: g.seasonMonths,
    credits: g.credits,
    closedCanopy: closed,
    restoredCanopies: restoredClosed,
    newCanopies: restoredClosed,
    canopyClosures: g.ledgerHistory.filter(entry => entry.outcome === 'canopy').length,
    youngPlots: young,
    invadedPlots: invaded,
    openCommitments: g.commitments.length,
    burnedPlots: g.burned.length,
    burnedPlotIds: [...g.burned],
    burnedArea: g.burned.length * PLOT_AREA_M2,
    fireEvents: g.burnedRecords.length,
    status: g.status,
  };
}

function shortState(p) {
  return p.state === 'closed' ? 'closed canopy' : p.state === 'young' ? `young canopy ${Math.round(p.canopy * 100)}%` : p.state === 'cleared' ? `cleared ground (${Math.round(p.grass * 100)}% grass)` : 'invasive fuel';
}

export function observe(g) {
  const m = metrics(g);
  const plots = Object.values(g.plots).map(p => {
    const job = jobFor(p);
    const q = job ? quote(g, job, p.id) : { valid: false, cost: 0, returns: 0, reason: 'No productive action.' };
    return { id: p.id, coordinate: p.coordinate, name: p.name, state: p.state, line: `${p.coordinate} ${p.name}: ${shortState(p)}. ${p.last}`, job, cost: q.cost, returns: q.returns, affordable: q.valid, shelter: round(shelter(g, p.id)), grass: round(p.grass), weeds: round(p.grass), canopy: round(p.canopy * 100), burned: p.burned };
  });
  const lines = [`${m.months} months elapsed; ${m.credits} credits; ${m.restoredCanopies} restored canopies (${m.closedCanopy} including shelter forest); ${m.burnedPlots} burned plots.`, `${m.openCommitments} open commitment${m.openCommitments === 1 ? '' : 's'} (cap ${CONFIG.commitmentCap}).`, ...plots.filter(p => p.job || p.burned).map(p => p.line)];
  return { version: VERSION, seed: g.seed, turn: g.turn, limit: g.limit, season: weather(g).label, status: g.status, metrics: m, credits: g.credits, lines, plots, ledger: ledger(g), ledgerHistory: cloneValue(g.ledgerHistory), latest: cloneValue(g.lastEvents), goal: 'Restore three canopies while learning how grass, shelter and fire interact.', note: 'Each REMOVE or RESTORE action advances six months. Looking is free.' };
}

export function studyPlot(g, id) {
  const actual = asId(id);
  if (actual == null || !g.plots[actual]) throw Error('Choose an active WORLD plot.');
  const p = g.plots[actual];
  const w = plotWeather(g, actual);
  const neighbours = neighbourIds(actual).map(n => { const q = g.plots[n]; return { id: n, coordinate: coordinate(n), state: q.state, canopy: Math.round(q.canopy * 100), grass: Math.round(q.grass * 100), shelter: round(shelter(g, n)) }; });
  const world = byId.get(actual);
  const localShelter = round(shelter(g, actual));
  const succession = {
    kind: p.state === 'young' ? 'young' : p.state === 'cleared' ? 'clearing' : p.state === 'closed' ? 'closed' : 'invaded',
    nativeFraction: p.state === 'closed' ? 1 : p.state === 'young' ? round(p.canopy) : 0,
    invasive: round(p.grass),
    heightScale: p.state === 'closed' ? round(Math.max(.55, p.canopy)) : p.state === 'young' ? round(.13 + .87 * p.canopy) : .13,
    year: Math.max(.5, g.seasonMonths / 12),
    maintained: p.state === 'closed' || (p.state === 'young' && p.grass < .3),
    moisture: round(effectiveMoisture(p)),
    exposure: round(effectiveExposure(p)),
  };
  return { id: actual, active: true, coordinate: coordinate(actual), name: p.name, state: p.state, weather: w, grass: round(p.grass), canopy: round(p.canopy), weeds: round(p.grass), shelter: localShelter, succession, nativeLoss: p.nativeLoss, burned: p.burned, moisture: round(effectiveMoisture(p)), exposure: round(effectiveExposure(p)), fuel: p.fuel, invasive: p.invasive, habitat: p.habitat, people: p.people, speciesIds: [...(world.speciesIds || [])], disturbance: world.disturbance || null, neighbours, fieldNote: p.state === 'young' ? 'Young trees are vulnerable to grass, dry weather and fire.' : p.state === 'cleared' ? 'The commitment remains open until restoration or returning grass resolves it.' : p.state === 'closed' ? 'Closed native canopy is shelter, not a guarantee against fire.' : 'Invasive fuel can return after removal if the opening stays unplanted.' };
}

function parseMove(move) {
  if (typeof move === 'string') {
    const [verb, id] = move.split(':');
    return { verb, id: id ?? null };
  }
  if (move && typeof move === 'object') return { verb: move.verb || move.action, id: move.id ?? move.plot ?? null };
  throw Error('Replay moves must be strings like remove:C2 or {verb,id}.');
}

export function replay(seed, moves = [], foundation = null) {
  const g = newGame(seed, foundation);
  for (const move of moves) {
    const parsed = parseMove(move);
    if (g.status !== 'playing') break;
    act(g, parsed.verb, parsed.id);
  }
  return g;
}
