#!/usr/bin/env python3
"""Safely audit or prune *verified* HomeLab storage backup snapshots on macOS.

Dry-run is the default. This script never modifies incomplete, unverified, or
unexpectedly named directories; deletion requires an explicit --apply flag.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

STAMP = re.compile(r"^\d{8}T\d{6}Z$")
HASH_ENTRY = re.compile(r"^([0-9a-fA-F]{64})  files\.tar\.gz$")


def mounted_volume(path):
    """Prevent writing to an internal-disk /Volumes placeholder."""
    if sys.platform != "darwin":
        return False
    if not path.is_dir() or path.is_symlink():
        return False
    mounts = subprocess.run(["/sbin/mount"], check=True, capture_output=True, text=True).stdout
    return " on {} (".format(path) in mounts


def verified_snapshot(path):
    if not path.is_dir() or path.is_symlink() or not STAMP.fullmatch(path.name):
        return False
    archive = path / "files.tar.gz"
    digest_file = path / "files.tar.gz.sha256"
    if any(p.is_symlink() for p in (archive, digest_file)):
        return False
    if not archive.is_file() or not digest_file.is_file():
        return False
    try:
        m = HASH_ENTRY.fullmatch(digest_file.read_text(encoding="ascii").strip())
        if not m:
            return False
        sha = hashlib.sha256()
        with archive.open("rb") as fp:
            while True:
                chunk = fp.read(1024 * 1024)
                if not chunk:
                    break
                sha.update(chunk)
        return sha.hexdigest() == m.group(1).lower()
    except (OSError, UnicodeError):
        return False


def plan_verified_snapshots(root, keep):
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Backup directory is missing or a symlink")
    snapshots = []
    ignored = []
    for entry in root.iterdir():
        if verified_snapshot(entry):
            snapshots.append(entry)
        else:
            ignored.append(entry)
    snapshots.sort(key=lambda x: x.name, reverse=True)
    return snapshots[:keep], snapshots[keep:], ignored


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", type=int, default=14, help="number of most recent verified backups to preserve (default 14)")
    parser.add_argument("--apply", action="store_true", help="delete only old verified backups after preview")
    args = parser.parse_args(argv)
    if args.keep < 2:
        parser.error("--keep must be at least 2")
    volume_path = os.environ.get("HOMELAB_VOLUME")
    if not volume_path:
        parser.error("set HOMELAB_VOLUME to the external SSD mount path")
    volume = Path(volume_path)
    if not mounted_volume(volume):
        print("ERROR: external SSD is not mounted: {}".format(volume), file=sys.stderr)
        return 2
    root = volume / "HomeLab" / "Backups" / "lab-storage"
    try:
        retained, removable, ignored = plan_verified_snapshots(root, args.keep)
    except (OSError, ValueError) as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 2
    action = "APPLY" if args.apply else "DRY RUN"
    print("RETENTION {}: {} verified backup(s), keeping newest {}, eligible for deletion: {}".format(
        action, len(retained) + len(removable), args.keep, len(removable)))
    if ignored:
        print("Skipped {} unverified/incomplete/other item(s); these will never be deleted by retention.".format(len(ignored)))
    for snapshot in removable:
        print("{} {}".format("DELETE" if args.apply else "WOULD DELETE", snapshot.name))
        if args.apply:
            # Snapshot path is a direct child of the expected root and was
            # confirmed to be a real directory with a valid SHA-256 archive.
            if snapshot.parent != root or not verified_snapshot(snapshot):
                print("ERROR: backup changed; refusing deletion: {}".format(snapshot), file=sys.stderr)
                return 3
            shutil.rmtree(str(snapshot))
    if args.apply:
        print("RETENTION COMPLETE: {} old verified backup(s) removed.".format(len(removable)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
