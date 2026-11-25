#!/usr/bin/env python3
"""Run one scheduled HomeLab backup at a time, with clear status logging.

Uses an OS-managed advisory file lock. It releases on process exit or a crash,
so no stale lock-directory cleanup is required.
"""
import datetime
import fcntl
from pathlib import Path
import subprocess
import sys


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(message, stream=sys.stdout):
    print("[{}] {}".format(stamp(), message), file=stream, flush=True)


def main():
    app = Path.home() / "Library" / "Application Support" / "HomeLab"
    bin_dir = app / "bin"
    backup = bin_dir / "backup-storage.sh"
    retention = bin_dir / "backup-retention.py"
    if not backup.is_file() or not retention.is_file():
        log("FAILED: installed backup/retention tool missing; rerun installer", sys.stderr)
        return 2
    app.mkdir(parents=True, exist_ok=True)
    lock_path = app / "backup.lock"
    with lock_path.open("a+") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("SKIPPED: another scheduled backup is already running", sys.stderr)
            return 75
        log("START HomeLab storage backup")
        try:
            result = subprocess.run(["/bin/bash", str(backup)], check=False)
        except OSError as exc:
            log("FAILED: could not execute backup: {}".format(exc), sys.stderr)
            return 2
        if result.returncode:
            log("FAILED HomeLab storage backup (exit {})".format(result.returncode), sys.stderr)
            return result.returncode
        log("SUCCESS HomeLab storage backup")
        # Report retention candidates only. No automatic deletion until user
        # explicitly reviews the dry run and opts in with --apply.
        try:
            audit = subprocess.run([sys.executable, str(retention), "--keep", "14"], check=False)
        except OSError as exc:
            log("WARNING retention preview could not start: {}".format(exc), sys.stderr)
            return 0
        if audit.returncode:
            log("WARNING retention preview failed (exit {}); backup is still verified".format(audit.returncode), sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
