/* Main thread: owns the terminal and the keyboard, hands lines to the worker.
 *
 * The game is a plain synchronous Python loop that calls input(). We keep it
 * that way by parking the worker on Atomics.wait until a line is ready here.
 * Line editing (echo, backspace) lives on this side because the worker is
 * blocked and cannot echo for us.
 */
// Measured from the real game: the widest screen is 78 columns and the tallest
// (the board plus a `help` listing under it) is 40 lines. A little headroom so
// nothing ever scrolls, since the game repaints by clearing and homing.
const COLS = 80;
const ROWS = 42;
const INPUT_BYTES = 4096;

const el = {
  boot: document.getElementById("boot"),
  fail: document.getElementById("fail"),
  failMsg: document.getElementById("fail-msg"),
  term: document.getElementById("term"),
};

/* --- the canopy doubles as the progress bar --------------------------------
   Foliage hangs from above the wordmark and creeps downward over it as the
   game loads. It is built out of the same 10px pixels as the letters so the
   whole screen reads as one grid. Deterministic noise, so it looks the same
   every visit rather than reshuffling on each refresh. */
const SVG_NS = "http://www.w3.org/2000/svg";
const canopy = document.getElementById("canopy");
const PX = 10, TOP = -110, LEFT = -30, RIGHT = 560;

function noise(seed) {
  let s = seed >>> 0;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
}

const rand = noise(20260722);
const pix = [];   // {x, y, row, leaf} — row drives the reveal order

// A ragged band of leaves along the top, uneven on both edges so it reads as
// foliage rather than a bar.
for (let x = LEFT; x <= RIGHT; x += PX) {
  const lift = rand() < 0.35 ? 1 : 0;
  const depth = 2 + Math.floor(rand() * 3);
  for (let r = -lift; r < depth; r++) {
    pix.push({ x, y: TOP + r * PX, row: r + lift, leaf: r < depth - 1 });
  }
}

// Strands trailing down out of the band, wandering as they fall and draping
// over the wordmark below.
for (let i = 0; i < 13; i++) {
  let x = LEFT + i * 45 + Math.round(rand() * 2) * PX;
  const len = 8 + Math.floor(rand() * 17);
  for (let r = 3; r < len; r++) {
    if (r > 3 && rand() < 0.28) x += rand() < 0.5 ? -PX : PX;
    pix.push({ x, y: TOP + r * PX, row: r });
    if (r > 4 && rand() < 0.3) {
      const side = rand() < 0.5 ? -PX : PX;
      pix.push({ x: x + side, y: TOP + r * PX, row: r, leaf: true });
      if (rand() < 0.35) pix.push({ x: x + side, y: TOP + (r - 1) * PX, row: r, leaf: true });
    }
  }
}

pix.sort((a, b) => a.row - b.row);          // grow strictly downward
const cells = pix.map((p) => {
  const el = document.createElementNS(SVG_NS, "rect");
  el.setAttribute("x", p.x);
  el.setAttribute("y", p.y);
  el.setAttribute("width", 9);
  el.setAttribute("height", 9);
  el.setAttribute("class", p.leaf ? "vpx leaf" : "vpx");
  canopy.appendChild(el);
  return el;
});

let growTarget = 0.06;   // how far down the canopy is headed
let grown = 0;           // where it actually is, easing toward the target

function grow() {
  grown += (growTarget - grown) * 0.045;
  const n = Math.round(grown * cells.length);
  cells.forEach((c, i) => c.classList.toggle("on", i < n));
  if (grown < 0.999) requestAnimationFrame(grow);
}
requestAnimationFrame(grow);

function die(msg) {
  el.boot.hidden = true;
  growTarget = grown;
  el.fail.hidden = false;
  el.failMsg.textContent = msg;
}

if (!crossOriginIsolated) {
  die(
    "This page needs cross-origin isolation to run Python.\n\n" +
    "Serve it with these headers:\n" +
    "  Cross-Origin-Opener-Policy: same-origin\n" +
    "  Cross-Origin-Embedder-Policy: require-corp\n\n" +
    "Locally: python3 web/serve.py"
  );
  throw new Error("not cross-origin isolated");
}

/* --- terminal -------------------------------------------------------------- */
const term = new Terminal({
  cols: COLS,
  rows: ROWS,
  cursorBlink: true,
  convertEol: true,          // the game prints "\n", not "\r\n"
  fontFamily: '"DejaVu Sans Mono", "Menlo", "Consolas", ui-monospace, monospace',
  fontSize: 16,
  lineHeight: 1.0,
  scrollback: 0,
  theme: { background: "#0d1410", foreground: "#cfe3d4", cursor: "#ff6a3d" },
});
term.open(el.term);

/* Scale the fixed 80-column grid to fill the window. Scaling rather than
   reflowing keeps every hand-aligned column in render.py exactly where it is. */
function fit() {
  el.term.style.transform = "scale(1)";
  const w = el.term.offsetWidth;
  const h = el.term.offsetHeight;
  if (!w || !h) return;
  const pad = 24;
  const s = Math.min((innerWidth - pad) / w, (innerHeight - pad) / h);
  el.term.style.transform = `scale(${s})`;
  el.term.parentElement.style.width = `${w * s}px`;
  el.term.parentElement.style.height = `${h * s}px`;
}
addEventListener("resize", fit);

/* --- stdin plumbing -------------------------------------------------------- */
const sab = new SharedArrayBuffer(8 + INPUT_BYTES);
const ctrl = new Int32Array(sab, 0, 2);
const data = new Uint8Array(sab, 8);
const enc = new TextEncoder();

let needInput = false;      // the worker is parked waiting for a line
let buf = "";               // the line being typed
const queue = [];           // completed lines not yet consumed

function deliver() {
  if (!needInput || queue.length === 0) return;
  const bytes = enc.encode(queue.shift() + "\n");
  const n = Math.min(bytes.length, data.length);
  data.set(bytes.subarray(0, n));
  Atomics.store(ctrl, 1, n);
  Atomics.store(ctrl, 0, 1);
  Atomics.notify(ctrl, 0);
  needInput = false;
}

term.onData((d) => {
  for (const ch of d) {
    if (ch === "\r" || ch === "\n") {
      term.write("\r\n");
      queue.push(buf);
      buf = "";
      deliver();
    } else if (ch === "\x7f" || ch === "\b") {
      if (buf) {
        buf = buf.slice(0, -1);
        term.write("\b \b");
      }
    } else if (ch === "\x1b") {
      break;                    // swallow arrow/escape sequences; input is line-based
    } else if (ch >= " ") {
      buf += ch;
      term.write(ch);
    }
  }
});

/* --- worker ---------------------------------------------------------------- */
// How far up the P the vine has climbed at each stage of the boot.
const STAGE = { "loading python": 0.42, "loading the valley": 0.8, ready: 1 };
const worker = new Worker("worker.js");

worker.onmessage = (e) => {
  const m = e.data;
  if (m.t === "stdout") {
    term.write(m.bytes);
  } else if (m.t === "want-input") {
    needInput = true;
    deliver();
  } else if (m.t === "status") {
    growTarget = STAGE[m.text] || growTarget;
  } else if (m.t === "ready") {
    growTarget = 1;
    // Let the vine finish curling before the title gives way to the game.
    setTimeout(() => el.boot.classList.add("gone"), 900);
    setTimeout(() => { el.boot.hidden = true; fit(); term.focus(); }, 1700);
  } else if (m.t === "exit") {
    term.write("\r\n\x1b[2m  the season is over. refresh to play again.\x1b[0m\r\n");
  } else if (m.t === "error") {
    die(m.text);
  }
};

// ?argv=--level+1 style passthrough, handy for testing a single level.
const argv = (new URLSearchParams(location.search).get("argv") || "").split(" ").filter(Boolean);
worker.postMessage({ t: "boot", sab, argv });
fit();
addEventListener("click", () => term.focus());
