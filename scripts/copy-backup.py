#!/usr/bin/env python3
"""Verify and copy a completed HomeLab backup to a private independent mount."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import errno
import fcntl
import hashlib
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile

MANIFESTS = {
    "storage": ("files.tar.gz.sha256", {"files.tar.gz"}),
    "monitoring": ("SHA256SUMS", {"prometheus.tar.gz", "grafana.tar.gz"}),
}


def require_regular(path):
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError(f"Expected a regular file: {path}")


def verify(directory, kind):
    manifest, archives = MANIFESTS[kind]
    manifest_path = directory / manifest
    require_regular(manifest_path)
    if manifest_path.stat().st_size > 4096:
        raise ValueError("Checksum manifest exceeds 4096 bytes")
    expected = {}
    for line in manifest_path.read_text(encoding="ascii").splitlines():
        match = re.fullmatch(r"([a-f0-9]{64}) [ *]([^ /]+)", line)
        if not match or match[2] not in archives or match[2] in expected:
            raise ValueError(f"Invalid entry in {manifest}")
        expected[match[2]] = match[1]
    if expected.keys() != archives:
        raise ValueError(f"Missing archive entries in {manifest}")
    for name, digest in expected.items():
        path = directory / name
        require_regular(path)
        with path.open("rb") as archive:
            if hashlib.file_digest(archive, "sha256").hexdigest() != digest:
                raise ValueError(f"SHA-256 mismatch: {path}")
    return expected


def run_id(name):
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", name):
        return False
    try:
        datetime.strptime(name, "%Y%m%dT%H%M%SZ")
    except ValueError:
        return False
    return True


def checked_mount(directory, mount, role):
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(f"{role} must be a real directory")
    directory = directory.resolve(strict=True)
    mount = mount.resolve(strict=True)
    if (not mount.is_mount() or not directory.is_relative_to(mount)
            or directory.stat().st_dev != mount.stat().st_dev):
        raise ValueError(f"{role} is outside the specified mounted filesystem")
    return directory


@contextmanager
def locked_destination(destination, mount, source):
    destination = checked_mount(destination, mount, "Destination")
    attrs = destination.stat()
    if attrs.st_uid != os.geteuid() or stat.S_IMODE(attrs.st_mode) != 0o700:
        raise ValueError("Destination directory must be owned by the current user and have permissions 0700")
    if source.stat().st_dev == attrs.st_dev:
        raise ValueError("Source and destination reside on the same filesystem")
    fd = os.open(destination, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not os.path.samestat(os.fstat(fd), destination.stat()):
            raise ValueError("Destination directory changed while obtaining the backup lock")
        yield destination
    finally:
        os.close(fd)


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def copy_run(source, final, kind, reserve, expected):
    manifest, archives = MANIFESTS[kind]
    names = sorted(archives | {manifest})
    needed = sum((source / name).stat().st_size for name in names) + reserve
    free = shutil.disk_usage(final.parent).free
    if free < needed:
        raise OSError(errno.ENOSPC, f"insufficient space: need {needed} bytes including reserve, have {free}")
    with tempfile.TemporaryDirectory(prefix=".partial-", dir=final.parent) as temp:
        stage = Path(temp) / "backup"
        stage.mkdir(mode=0o700)
        for name in names:
            with (source / name).open("rb") as original, (stage / name).open("xb") as copied:
                os.fchmod(copied.fileno(), 0o600)
                shutil.copyfileobj(original, copied)
                copied.flush()
                os.fsync(copied.fileno())
        if verify(stage, kind) != expected:
            raise ValueError("Destination manifest differs from the verified source")
        if shutil.disk_usage(final.parent).free < reserve:
            raise OSError(errno.ENOSPC, "destination free space fell below the configured reserve")
        sync_directory(stage)
        stage.rename(final)
        sync_directory(final.parent)


def copy_backup(source, destination, kind, destination_mount, reserve=0):
    if not run_id(source.name):
        raise ValueError("Source directory must have a UTC backup run ID")
    if source.is_symlink() or not source.is_dir():
        raise ValueError("Source must be a real directory")
    source = source.resolve(strict=True)
    with locked_destination(destination, destination_mount, source) as destination:
        final = destination / f"{kind}-{source.name}"
        if final.exists() or final.is_symlink():
            raise FileExistsError(f"Backup copy already exists: {final}")
        copy_run(source, final, kind, reserve, verify(source, kind))
        return final


def log(level, message):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    output = sys.stderr if level == "ERROR" else sys.stdout
    print(f"{stamp} {level} {message}", file=output, flush=True)


def replicate(source, source_mount, destination, destination_mount, kind, reserve, keep):
    source = checked_mount(source, source_mount, "Source")
    copied = existing = deferred = failed = 0
    verified_copies = set()
    with locked_destination(destination, destination_mount, source) as destination:
        for run in sorted(source.iterdir(), reverse=True):
            if not run_id(run.name):
                continue
            try:
                checked_mount(run, source_mount, "Backup run")
                manifest = run / MANIFESTS[kind][0]
                if not manifest.exists() and not manifest.is_symlink():
                    log("DEFER", f"{run.name} has no completion manifest")
                    deferred += 1
                    continue
                expected = verify(run, kind)
                final = destination / f"{kind}-{run.name}"
                if final.exists() or final.is_symlink():
                    checked_mount(final, destination_mount, "Existing copy")
                    if verify(final, kind) != expected:
                        raise ValueError("Existing copy differs from the source; investigate before replacing")
                    existing += 1
                    log("VERIFIED", f"{kind} {run.name} already copied")
                else:
                    copy_run(run, final, kind, reserve, expected)
                    copied += 1
                    log("COPIED", f"{kind} {run.name} passed source and destination SHA-256")
                verified_copies.add(final.name)
            except (OSError, ValueError) as exc:
                failed += 1
                log("ERROR", f"{kind} {run.name}: {exc}")

        if copied + existing == 0 and failed == 0:
            log("ERROR", "no completed source backup runs were verified")
            failed += 1

        if keep is not None:
            if failed == 0:
                for candidate in sorted(destination.glob(f"{kind}-*"), reverse=True):
                    if candidate.name in verified_copies or not run_id(candidate.name.removeprefix(f"{kind}-")):
                        continue
                    try:
                        checked_mount(candidate, destination_mount, "Retention candidate")
                        verify(candidate, kind)
                        verified_copies.add(candidate.name)
                    except (OSError, ValueError) as exc:
                        failed += 1
                        log("ERROR", f"retention preview for {candidate.name}: {exc}")
            if failed:
                log("RETENTION", "preview withheld because verification failed")
            else:
                older = sorted(verified_copies, reverse=True)[keep:]
                log("RETENTION", f"keeping newest {keep}; {len(older)} older verified copies for review")
                for name in older:
                    log("RETENTION", f"preview only: {name}")

    log("SUMMARY", f"{kind}: copied={copied} already_verified={existing} deferred={deferred} failed={failed}")
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=MANIFESTS)
    parser.add_argument("source", type=Path, help="completed run, or parent directory with --all-completed")
    parser.add_argument("destination", type=Path, help="existing private directory, mode 0700")
    parser.add_argument("--destination-mount", type=Path, required=True)
    parser.add_argument("--confirm-independent", action="store_true",
                        help="confirm the mounted destination is on different physical media")
    parser.add_argument("--all-completed", action="store_true",
                        help="replicate all completed runs idempotently for scheduling")
    parser.add_argument("--source-mount", type=Path, help="expected source mount for recurring replication")
    parser.add_argument("--reserve-mib", type=int, help="minimum destination free space left after a copy")
    parser.add_argument("--keep", type=int, help="preview older verified copies outside this count")
    args = parser.parse_args()
    if not args.confirm_independent:
        parser.error("verify physical media and supply --confirm-independent")
    if args.all_completed != bool(args.source_mount):
        parser.error("--all-completed and --source-mount must be supplied together")
    if args.keep is not None and (not args.all_completed or args.keep < 1):
        parser.error("--keep requires --all-completed and a positive number")
    if args.reserve_mib is not None and args.reserve_mib < 0:
        parser.error("--reserve-mib must be nonnegative")
    reserve_mib = args.reserve_mib if args.reserve_mib is not None else (64 if args.all_completed else 0)
    reserve = reserve_mib * 1024**2
    try:
        if args.all_completed:
            log("START", f"{args.kind} replication (reserve {reserve_mib} MiB)")
            return replicate(args.source, args.source_mount, args.destination,
                             args.destination_mount, args.kind, reserve, args.keep)
        final = copy_backup(args.source, args.destination, args.kind, args.destination_mount, reserve)
    except BlockingIOError as exc:
        if exc.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
            log("ERROR", "destination is locked by another copy invocation")
            return 75
        log("ERROR", f"backup copy failed: {exc}")
        return 1
    except (OSError, ValueError) as exc:
        log("ERROR", f"backup copy failed: {exc}")
        return 1
    print(f"Verified source and destination SHA-256: {final}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
