"""Start the backend as a true daemon (survives the terminal that launched it).

    python start_daemon.py          -> starts on 127.0.0.1:8000
    python start_daemon.py stop     -> stops it
"""
import os
import signal
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).parent
PYTHON = BACKEND / ".venv" / "bin" / "python"
LOG = BACKEND / "backend_server.log"
PIDFILE = BACKEND / "backend.pid"
PORT = 8000


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
        os.setsid()                     # new session: immune to terminal teardown
        pid2 = os.fork()
        if pid2 == 0:                   # grandchild = the daemon
            os.dup2(log_fd, 1)
            os.dup2(log_fd, 2)
            devnull = os.open(os.devnull, os.O_RDONLY)
            os.dup2(devnull, 0)
            os.execv(str(PYTHON), [str(PYTHON), "-m", "uvicorn", "app.main:app",
                                   "--host", "127.0.0.1", "--port", str(PORT)])
        os._exit(0)
    os.waitpid(pid1, 0)                 # parent: reap first child

    # wait for the port to come up
    for _ in range(20):
        time.sleep(0.5)
        if os.path.exists(LOG) and "Uvicorn running" in LOG.read_text(errors="ignore"):
            break
    # find the daemon pid via pidfile written below
    pids = os.popen(f"lsof -ti tcp:{PORT} -sTCP:LISTEN").read().split()
    if pids:
        PIDFILE.write_text(pids[0])
        print(f"✅ backend daemon running: pid {pids[0]}  http://127.0.0.1:{PORT}  (logs: {LOG.name})")
    else:
        print("❌ failed to start - check backend_server.log")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop()
    else:
        start()
