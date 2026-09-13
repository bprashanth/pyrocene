/* camera.js: shots. Each beat gets a camera move, a function of its own
 * progress, and the player blends from wherever the camera was into it so
 * nothing jumps unless a cut is wanted. */
import * as THREE from "three";

const clamp = (x, a, b) => x < a ? a : x > b ? b : x;
const smooth = t => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };

export function makeShots(world, groundY) {
  const { cols, rows } = world;
  const centre = new THREE.Vector3(cols / 2, 0, rows / 2);
  function centroid(cells) { let x = 0, z = 0; for (const i of cells) { x += i % cols + 0.5; z += Math.floor(i / cols) + 0.5; } return [x / cells.length, z / cells.length]; }
  function extent(cells) { let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9; for (const i of cells) { const c = i % cols, r = Math.floor(i / cols); x0 = Math.min(x0, c); x1 = Math.max(x1, c + 1); z0 = Math.min(z0, r); z1 = Math.max(z1, r + 1); } return Math.max(x1 - x0, z1 - z0); }

  // a pose from a target, a distance, an azimuth (radians, 0 = looking north
  // from the south), an elevation angle
  function orbit(tx, tz, dist, az, el, fov) {
    const ty = groundY(clamp(tx, 0, cols), clamp(tz, 0, rows)) + 0.4;
    const px = tx + dist * Math.cos(el) * Math.sin(az), pz = tz + dist * Math.cos(el) * Math.cos(az), py = ty + dist * Math.sin(el);
    const gy = groundY(clamp(px, 0, cols), clamp(pz, 0, rows));
    return { pos: [px, Math.max(py, gy + 1.25), pz], target: [tx, ty, tz], fov: fov || 42 };
  }
  function focusCells(b) {
    if (b.kind === "burn" || b.kind === "after" || b.kind === "flash") return b.fire.cells;
    if (b.kind === "ignite") return [b.ign];
    if (b.kind === "held") return b.held.concat(b.pressed);
    if (b.kind === "cut" && b.split) return b.stand;
    return b.focus || b.cut || b.stand || null;
  }
  const wideDist = Math.max(cols, rows * 1.9) * 0.72;
  // the homes the fire reached: the village square nearest the last fire that reached one
  const endVillage = [];
  if (((world.log.game.ending || {}).reason) === "village") {
    const b0 = world.frames[0].board; const vill = [];
    for (let i = 0; i < b0.cover.length; i++) if (b0.cover[i] === 4) vill.push(i);
    const hit = [...world.nights].reverse().find(nt => nt.fire && nt.fire.village_reached);
    if (hit && vill.length) {
      const burned = hit.fire.burned_cells.map(x => globalThis.PyroLog.parseCell(x, cols));
      const near = vill.map(v => [v, Math.min(...burned.map(b => Math.hypot(b % cols - v % cols, Math.floor(b / cols) - Math.floor(v / cols))))]).sort((a, b) => a[1] - b[1]);
      const best = near[0][0];
      for (const [v, d] of near) if (Math.hypot(v % cols - best % cols, Math.floor(v / cols) - Math.floor(best / cols)) <= 2) endVillage.push(v);
    } else endVillage.push(...vill);
  }

  function shot(b) {
    const cells = focusCells(b);
    const [cx, cz] = cells && cells.length ? centroid(cells) : [cols / 2, rows / 2];
    const ext = cells && cells.length ? extent(cells) : Math.max(cols, rows);
    const seed = (b.i * 0.618) % 1;
    switch (b.kind) {
      case "end":
        if (endVillage.length) { const [vx, vz] = centroid(endVillage); return p => orbit(vx, vz, 6.5 - 0.5 * p, -0.6 + 0.5 * p, 0.6, 38); }
      case "open":
        return p => orbit(cols / 2, rows / 2 + 0.5, wideDist * (1.02 - 0.06 * p), 0.18 - 0.08 * p, 0.5, 42);
      case "rewind":
        return p => orbit(cols / 2, rows / 2, wideDist * 1.05, -0.3 + 0.2 * p, 0.7, 40);
      case "hold":
        return b.night === 0 ? p => orbit(cols / 2, rows / 2, wideDist * 1.05, -0.5 + 0.35 * p, 0.6, 42)
                             : p => orbit(cols / 2, rows / 2, wideDist * 0.9, 0.1 + 0.1 * p, 0.55, 42);
      case "clear": case "taken":
        return p => orbit(cx, cz, 4.5 + ext * 0.9, (seed - 0.5) * 1.6 + 0.25 * p, 0.55, 40);
      case "dig":
        return p => orbit(cx, cz, 4.5 + ext * 0.7, (seed - 0.5) * 2.0 + 0.45 * p, 0.62, 38);
      case "water": case "ews": case "quiet":
        return p => orbit(cols / 2, rows / 2, wideDist * 0.85, 0.2 + 0.08 * p, 0.5, 42);
      case "grow":
        return p => orbit(cx, cz, 6 + ext * 0.75 - 1.2 * p, (seed - 0.5) * 1.2 + 0.15 * p, 0.5, 42);
      case "connected": case "fuel":
        return p => orbit(cx, cz, 4 + ext * 1.0 + 1.5 * p, -0.6 + 0.9 * p, 0.35 + 0.3 * p, 40);
      case "ignite":
        return p => orbit(cx, cz, 5.0 + 0.5 * p, (seed - 0.5) * 3 + 0.12 * p, 0.42 + 0.05 * p, 36);
      case "burn":
        return p => orbit(cx, cz, 4.5 + ext * 0.9 + 1.5 * p, (seed - 0.5) * 2.4 + 0.3 * p, 0.3 + 0.12 * p, 40);
      case "held": {
        // from the burning side, looking across the line into the forest it saved
        const [hx, hz] = centroid(b.held), [px, pz] = centroid(b.pressed);
        const az = Math.atan2(px - hx, pz - hz);
        return p => orbit(hx, hz, 4.8 + ext * 0.35, az + 0.35 - 0.3 * p, 0.52 + 0.05 * p, 38);
      }
      case "capped": case "village":
        return p => orbit(cx, cz, 4 + ext * 0.7, (seed - 0.5) * 2 + 0.3 * p, 0.3, 38);
      case "after":
        return p => orbit(cx, cz, 5 + ext * 0.9 + 6 * p, (seed - 0.5) * 2 + 0.2 * p, 0.32 + 0.3 * p, 40);
      case "crit":
        return b.final ? p => orbit(cols / 2, rows / 2, wideDist * 0.95, 0.1 + 0.05 * p, 0.6, 40)
                       : p => orbit(cx, cz, 5 + ext * 0.9, -0.7 + 0.5 * p, 0.45, 40);
      case "cut":
        return p => orbit(cx, cz, 4.2 + ext * 0.7, -0.4 + 0.35 * p, 0.38 + 0.08 * p, 38);
      default:
        return p => orbit(cols / 2, rows / 2, wideDist, 0.1, 0.55, 42);
    }
  }
  const CUTS = new Set(["ignite", "held", "crit", "cut", "fuel", "connected", "burn"]);
  return { shot, isCut: b => CUTS.has(b.kind), centre };
}

export function lerpPose(a, b, t) {
  const l = (x, y) => x + (y - x) * t;
  return { pos: [l(a.pos[0], b.pos[0]), l(a.pos[1], b.pos[1]), l(a.pos[2], b.pos[2])], target: [l(a.target[0], b.target[0]), l(a.target[1], b.target[1]), l(a.target[2], b.target[2])], fov: l(a.fov, b.fov) };
}
export { smooth };
