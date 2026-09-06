"""Start the CRA frontend as a daemon on port 3000.

    python start_frontend_daemon.py        -> npm start, background
    python start_frontend_daemon.py stop   -> kill it
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

APP = Path(__file__).parent
LOG = APP / "frontend.log"
PIDFILE = APP / "frontend.pid"
PORT = 3000


def read_pid():
    try:
        return int(PIDFILE.read_text().strip())
    except (OSError, ValueError):
        return None


def stop():
    pid = read_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            print(f"stopped frontend pid {pid}")
        except ProcessLookupError:
            print("stale pidfile")
        PIDFILE.unlink(missing_ok=True)
    else:
        print("not running")


def start():
    if read_pid():
        try:
            os.kill(read_pid(), 0)
            print(f"already running (pid {read_pid()})")
            return
        except ProcessLookupError:
            PIDFILE.unlink(missing_ok=True)

    log_fd = os.open(LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    pid1 = os.fork()
    if pid1 == 0:
        os.setsid()
        pid2 = os.fork()
        if pid2 == 0:
            os.dup2(log_fd, 1)
            os.dup2(log_fd, 2)
            devnull = os.open(os.devnull, os.O_RDONLY)
            os.dup2(devnull, 0)
            env = dict(os.environ, BROWSER="none", PORT=str(PORT))
            os.chdir(APP)
            os.execvp("npm", ["npm", "start"])
        os._exit(0)
    os.waitpid(pid1, 0)

    for _ in range(60):                    # webpack can take a while
        time.sleep(1)
        out = subprocess.run(
            ["lsof", "-ti", f"tcp:{PORT}", "-sTCP:LISTEN"],
            capture_output=True, text=True,
        ).stdout.strip()
        if out:
            PIDFILE.write_text(out.split()[0])
            print(f"✅ frontend running: pid {out.split()[0]}  http://localhost:{PORT}  (log: {LOG.name})")
            return
    print("❌ frontend did not come up in 60s - check frontend.log")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop()
    else:
        start()
