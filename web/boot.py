"""Browser bootstrap for the terminal game.

This file exists so that nothing under engine/ or terminal/ has to know the web
build exists. It papers over the three ways a browser is not a tty, then hands
control to terminal.play.main() exactly as the CLI would.

  1. termios/tty do not exist in Pyodide, and terminal/play.py imports them at
     module scope (for the dormant office phase). Stub them before the import.
  2. sys.stdout.isatty() decides whether colour is on. Pyodide's stdout is not a
     tty, so force it; xterm.js renders the ANSI perfectly well.
  3. Python block-buffers stdout when it is not a tty, which would swallow the
     animation beats until a screen finished. Write through on every call.
"""
import sys
import types

# --- 1. stub the tty modules ------------------------------------------------
if "termios" not in sys.modules:
    termios = types.ModuleType("termios")
    termios.TCSADRAIN = 1
    termios.error = OSError
    termios.tcgetattr = lambda fd: None
    termios.tcsetattr = lambda fd, when, attrs: None
    sys.modules["termios"] = termios

if "tty" not in sys.modules:
    tty = types.ModuleType("tty")
    tty.setcbreak = lambda fd, when=None: None
    tty.setraw = lambda fd, when=None: None
    sys.modules["tty"] = tty

# --- 2 & 3. make stdio behave like an interactive terminal -------------------
try:
    sys.stdout.reconfigure(write_through=True)
except Exception:
    pass

# The worker already passes isatty:true to Pyodide's setStdin/setStdout, so this
# is only a fallback for stream types that do not honour it. play.main() gates
# both the colour and the start menu on isatty, and a False here would silently
# drop the player into a plain-text sandbox level.
for _stream in (sys.stdout, sys.stdin):
    try:
        _stream.isatty = lambda: True
    except (AttributeError, TypeError):
        pass


def run(argv=None):
    """Entry point the worker calls. argv mirrors the CLI flags."""
    from terminal import play
    from terminal import render as R

    # main() derives colour from isatty. On the off chance the patch above did
    # not take, pin it on: xterm.js renders the ANSI either way.
    _set_color = R.set_color
    R.set_color = lambda on=True: _set_color(True)
    R.set_color(True)

    argv = list(argv or [])
    if "--selftest" in argv:
        return selftest()

    # --campaign drives the office phase, which needs raw per-keystroke input.
    # The browser only feeds us whole lines, so quietly drop it.
    argv = [a for a in argv if a != "--campaign"]

    sys.argv = ["pyrocene"] + argv
    try:
        play.main()
    except (EOFError, KeyboardInterrupt):
        print("\r\n")
    finally:
        print(R.RESET, end="")


def selftest():
    """Diagnostics for the stdio bridge, reachable at ?argv=--selftest.

    Checks the three things that silently break the game if the wiring is
    wrong: output flushes as it is written, time.sleep actually returns, and
    consecutive input() calls each get their own line.
    """
    print("write_through:", getattr(sys.stdout, "write_through", "n/a"), flush=True)
    print("line_buffering:", getattr(sys.stdout, "line_buffering", "n/a"), flush=True)
    print("stdout class:", type(sys.stdout).__name__, flush=True)
    print("stdin class:", type(sys.stdin).__name__, flush=True)
    print("stdout.isatty:", sys.stdout.isatty(), "stdin.isatty:", sys.stdin.isatty(), flush=True)
    sys.stdout.write("UNFLUSHED-MARKER-BEFORE-SLEEP\n")
    import time as _t
    _t.sleep(2.0)
    print("SLEPT-OK", flush=True)
    a = input("PROMPT-A> ")
    print("GOT-A:", repr(a), flush=True)
    b = input("PROMPT-B> ")
    print("GOT-B:", repr(b), flush=True)
    print("SELFTEST-DONE", flush=True)
