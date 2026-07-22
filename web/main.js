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

/* --- the creeper doubles as the progress bar ------------------------------- */
const vine = document.getElementById("vine");
const VINE_LEN = vine.getTotalLength();

/* Grow the leaves out of the path itself rather than placing them by hand: each
   sits exactly on the vine, angled along its tangent and alternating sides. */
const LEAF_AT = [0.18, 0.33, 0.47, 0.6, 0.72, 0.84, 0.93];
const leaves = LEAF_AT.map((t, i) => {
  const p = vine.getPointAtLength(VINE_LEN * t);
  const q = vine.getPointAtLength(VINE_LEN * Math.min(t + 0.02, 1));
  const deg = (Math.atan2(q.y - p.y, q.x - p.x) * 180) / Math.PI;
  const side = i % 2 ? 6 : -6;
  const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
  g.setAttribute("transform",
    `translate(${p.x} ${p.y}) rotate(${deg + (i % 2 ? 34 : -34)}) translate(9 ${side})`);
  const leaf = document.createElementNS("http://www.w3.org/2000/svg", "ellipse");
  leaf.setAttribute("class", "leaf");
  leaf.setAttribute("rx", 11);
  leaf.setAttribute("ry", 5.5);
  g.appendChild(leaf);
  vine.parentNode.appendChild(g);
  return leaf;
});
vine.style.strokeDasharray = VINE_LEN;
vine.style.strokeDashoffset = VINE_LEN;

let growTarget = 0.06;   // where the vine is headed
let grown = 0;           // where it actually is, easing toward the target

function grow() {
  grown += (growTarget - grown) * 0.045;
  vine.style.strokeDashoffset = (VINE_LEN * (1 - grown)).toFixed(2);
  // A leaf opens once the vine has grown past where it sits.
  leaves.forEach((leaf, i) =>
    leaf.classList.toggle("on", grown > LEAF_AT[i] + 0.04));
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
