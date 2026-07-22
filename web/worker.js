/* Pyodide worker: runs the unmodified Python game and blocks on stdin.
 *
 * The whole point of living in a worker is Atomics.wait, which is illegal on
 * the main thread. It lets input() genuinely block, so the game's ordinary
 * synchronous loop runs as-is with no async refactor.
 *
 * stdin  main thread -> SharedArrayBuffer -> Python
 * stdout Python -> postMessage(bytes) -> xterm.js
 */
const PYODIDE_VERSION = "0.28.3";
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

let ctrl = null;    // Int32Array view: [0] = ready flag, [1] = byte length
let data = null;    // Uint8Array view of the payload region
let pending = new Uint8Array(0);   // bytes of the current line not yet consumed

/** Block until the main thread hands us a line, as bytes including the newline. */
function awaitLine() {
  Atomics.store(ctrl, 0, 0);
  self.postMessage({ t: "want-input" });
  Atomics.wait(ctrl, 0, 0);
  const n = Atomics.load(ctrl, 1);
  const line = new Uint8Array(n);   // copy out; the SAB view cannot be handed on
  line.set(data.subarray(0, n));
  return line;
}

/* Pyodide's low-level stdin interface: fill `buffer`, return the byte count.
 * We deliberately avoid the higher-level `stdin` string callback, which routes
 * through its LegacyReader and leaves the stdout stream unusable after the
 * first read, so every write past the first prompt is silently dropped. */
function readInto(buffer) {
  if (pending.length === 0) pending = awaitLine();
  const n = Math.min(buffer.length, pending.length);
  buffer.set(pending.subarray(0, n));
  pending = pending.subarray(n);
  return n;                        // never 0: 0 would signal EOF
}

function out(buffer) {
  if (buffer.length === 0) return 0;
  // The buffer is reused by Pyodide, so copy before it crosses the boundary.
  const copy = new Uint8Array(buffer);
  self.postMessage({ t: "stdout", bytes: copy }, [copy.buffer]);
  return buffer.length;
}

function status(text) {
  self.postMessage({ t: "status", text });
}

async function boot(sab, argv) {
  ctrl = new Int32Array(sab, 0, 2);
  data = new Uint8Array(sab, 8);

  status("loading python");
  importScripts(PYODIDE_URL + "pyodide.js");
  const pyodide = await loadPyodide({ indexURL: PYODIDE_URL });

  status("loading the valley");
  const manifest = await (await fetch("py/manifest.json")).json();
  const files = await Promise.all(
    manifest.map((p) => fetch("py/" + p).then((r) => r.arrayBuffer()))
  );
  pyodide.FS.mkdirTree("/game");
  manifest.forEach((p, i) => {
    const dir = p.includes("/") ? "/game/" + p.slice(0, p.lastIndexOf("/")) : "/game";
    pyodide.FS.mkdirTree(dir);
    pyodide.FS.writeFile("/game/" + p, new Uint8Array(files[i]));
  });
  const bootSrc = await (await fetch("boot.py")).text();
  pyodide.FS.writeFile("/game/boot.py", bootSrc);

  // isatty matters: play.main() gates both colour and the start menu on it.
  pyodide.setStdin({ read: readInto, isatty: true });
  pyodide.setStdout({ write: out, isatty: true });
  pyodide.setStderr({ write: out, isatty: true });

  status("ready");
  self.postMessage({ t: "ready" });

  pyodide.runPython("import sys; sys.path.insert(0, '/game')");
  const boot = pyodide.pyimport("boot");
  boot.run(argv || []);
  self.postMessage({ t: "exit" });
}

self.onmessage = (e) => {
  if (e.data.t === "boot") {
    boot(e.data.sab, e.data.argv).catch((err) => {
      self.postMessage({ t: "error", text: String(err && err.stack || err) });
    });
  }
};
