"""Start the CRA frontend as a true daemon (double-fork + setsid, same recipe
as backend/start_daemon.py — immune to terminal/session teardown).

    python start_frontend_daemon.py          -> dev server on 127.0.0.1:3000
    python start_frontend_daemon.py stop     -> stops it
"""
import os
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
APP = ROOT / "fire-detection-app"
NODE_BIN = Path.home() / ".nvm" / "versions" / "node" / "v18.20.8" / "bin"
NPM = NODE_BIN / "npm"
LOG = ROOT / "frontend_dev.log"
PIDFILE = ROOT / "frontend.pid"
PORT = 3000


def read_pid():
    try:
        return int(PIDFILE.read_text().strip())
    except (OSError, ValueError):
        return None


def stop():
    pid = read_pid()
    if not pid:
        print("not running")
        return
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        print(f"stopped daemon pid {pid}")
    except ProcessLookupError:
        print("stale pidfile - cleaned")
    PIDFILE.unlink(missing_ok=True)


def start():
    if read_pid():
        try:
            os.kill(read_pid(), 0)
            print(f"already running (pid {read_pid()}) on port {PORT}")
            return
        except ProcessLookupError:
            PIDFILE.unlink(missing_ok=True)

    log_fd = os.open(LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    pid1 = os.fork()
    if pid1 == 0:                       # first child
        os.setsid()                     # new session: immune to teardown
        pid2 = os.fork()
        if pid2 == 0:                   # grandchild = the daemon
            os.dup2(log_fd, 1)
            os.dup2(log_fd, 2)
            devnull = os.open(os.devnull, os.O_RDONLY)
            os.dup2(devnull, 0)
            os.chdir(APP)
            env = dict(os.environ)
            env["PATH"] = f"{NODE_BIN}:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
            env["BROWSER"] = "none"
            os.execve(str(NPM), [str(NPM), "start"], env)
        os._exit(0)
    os.waitpid(pid1, 0)                 # parent: reap first child

    # wait for the port to come up
    for _ in range(40):
        time.sleep(0.5)
        pids = os.popen(f"lsof -ti tcp:{PORT} -sTCP:LISTEN").read().split()
        if pids:
            PIDFILE.write_text(pids[0])
            print(f"✅ frontend daemon running: pid {pids[0]}  http://localhost:{PORT}  (logs: {LOG.name})")
            return
    print("❌ failed to start - check frontend_dev.log")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop()
    else:
        start()
