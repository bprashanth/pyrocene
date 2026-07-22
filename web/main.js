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
  fill: document.getElementById("boot-fill"),
  status: document.getElementById("boot-status"),
  fail: document.getElementById("fail"),
  failMsg: document.getElementById("fail-msg"),
  term: document.getElementById("term"),
};

function die(msg) {
  el.boot.hidden = true;
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
const STAGE = { "loading python": 35, "loading the valley": 75, ready: 100 };
const worker = new Worker("worker.js");

worker.onmessage = (e) => {
  const m = e.data;
  if (m.t === "stdout") {
    term.write(m.bytes);
  } else if (m.t === "want-input") {
    needInput = true;
    deliver();
  } else if (m.t === "status") {
    el.status.textContent = m.text;
    el.fill.style.width = (STAGE[m.text] || 10) + "%";
  } else if (m.t === "ready") {
    el.boot.classList.add("gone");
    setTimeout(() => { el.boot.hidden = true; fit(); term.focus(); }, 500);
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
