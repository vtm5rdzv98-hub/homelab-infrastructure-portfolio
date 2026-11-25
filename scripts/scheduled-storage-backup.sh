#!/bin/bash
# HomeLab LaunchAgent entrypoint: run one backup with a crash-safe file lock.
set -euo pipefail
umask 077
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
exec /usr/bin/python3 "$HOME/Library/Application Support/HomeLab/bin/backup-orchestrator.py"
