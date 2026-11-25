#!/usr/bin/env python3
"""Extract a checked recovery archive into an empty, private scratch directory."""

from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile


def extract(archive, destination):
    if not destination.is_dir() or destination.is_symlink() or any(destination.iterdir()):
        raise ValueError("Recovery extraction requires an empty scratch directory")
    free = shutil.disk_usage(destination).free - 512 * 1024**2
    total = 0
    with tarfile.open(archive, "r:gz") as source:
        members = []
        for member in source:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not (member.isfile() or member.isdir()):
                raise ValueError("Recovery archive contains a path, link or special file outside the allowed format")
            total += member.size
            if total > free or total > 2 * 1024**3 or len(members) >= 100_000:
                raise ValueError("Recovery archive exceeds the scratch space or extraction limit")
            members.append(member)
        source.extractall(destination, members=members, filter="data")


if __name__ == "__main__":
    try:
        extract(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, ValueError, tarfile.TarError) as exc:
        sys.exit(f"Recovery extraction refused: {exc}")
