#!/bin/bash
# Disable the HomeLab user backup schedule without touching backup archives.
set -euo pipefail
[[ "$(uname -s)" == Darwin ]] || { echo 'Run on macOS.' >&2; exit 1; }
label='dev.homelab.storage-backup'
plist="$HOME/Library/LaunchAgents/$label.plist"
uid="$(id -u)"
if launchctl print "gui/$uid/$label" >/dev/null 2>&1; then
  launchctl bootout "gui/$uid" "$plist"
fi
rm -f "$plist"
printf 'Disabled scheduled backups. Existing backup archives and logs are unchanged.\n'
