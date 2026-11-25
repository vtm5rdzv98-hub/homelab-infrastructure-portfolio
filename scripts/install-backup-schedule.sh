#!/bin/bash
# Install or update a daily HomeLab storage backup for the currently logged-in Mac user.
# Set HOMELAB_VOLUME to the external SSD mount path before running.
# Usage: bash scripts/install-backup-schedule.sh [hour 0-23] [minute 0-59]
set -euo pipefail
[[ "$(uname -s)" == Darwin ]] || { echo 'Run this installer on macOS.' >&2; exit 1; }
hour="${1:-20}"
minute="${2:-0}"
[[ "$hour" =~ ^([0-9]|1[0-9]|2[0-3])$ && "$minute" =~ ^([0-9]|[1-5][0-9])$ ]] || { echo 'Usage: ... [hour 0-23] [minute 0-59]' >&2; exit 2; }
volume="${HOMELAB_VOLUME:?Set HOMELAB_VOLUME to the external SSD mount path}"
[[ "$volume" == /Volumes/* && -d "$volume/HomeLab" ]] || { echo 'Expected a mounted SSD with a HomeLab directory.' >&2; exit 2; }
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_backup="$project_root/scripts/backup-storage.sh"
source_runner="$project_root/scripts/scheduled-storage-backup.sh"
source_orchestrator="$project_root/scripts/backup-orchestrator.py"
source_retention="$project_root/scripts/backup-retention.py"
[[ -f "$source_backup" && -f "$source_runner" && -f "$source_orchestrator" && -f "$source_retention" ]] || { echo 'Missing backup scripts in the repository.' >&2; exit 2; }
label='dev.homelab.storage-backup'
app_support="$HOME/Library/Application Support/HomeLab/bin"
logs="$HOME/Library/Logs/HomeLab"
plist="$HOME/Library/LaunchAgents/$label.plist"
mkdir -p "$app_support" "$logs" "$HOME/Library/LaunchAgents"
chmod 700 "$HOME/Library/Application Support/HomeLab" "$app_support" "$logs"
install -m 700 "$source_backup" "$app_support/backup-storage.sh"
install -m 700 "$source_runner" "$app_support/scheduled-storage-backup.sh"
install -m 700 "$source_orchestrator" "$app_support/backup-orchestrator.py"
install -m 700 "$source_retention" "$app_support/backup-retention.py"
# Generate XML with Python's stdlib to avoid path-escaping bugs with spaces/& in HOME.
/usr/bin/python3 - "$plist" "$label" "$app_support/scheduled-storage-backup.sh" "$logs" "$hour" "$minute" "$volume" <<'PY'
import plistlib,sys
path, label, runner, logs, hour, minute, volume = sys.argv[1:]
config = {
  'Label': label,
  'ProgramArguments': ['/bin/bash', runner],
  'StartCalendarInterval': {'Hour': int(hour), 'Minute': int(minute)},
  'RunAtLoad': False,
  'StandardOutPath': logs + '/backup.log',
  'StandardErrorPath': logs + '/backup-error.log',
  'EnvironmentVariables': {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'HOMELAB_VOLUME': volume},
}
with open(path, 'wb') as f:
    plistlib.dump(config, f)
PY
chmod 600 "$plist"
plutil -lint "$plist"
uid="$(id -u)"
if launchctl print "gui/$uid/$label" >/dev/null 2>&1; then
  launchctl bootout "gui/$uid" "$plist"
fi
launchctl enable "gui/$uid/$label"
launchctl bootstrap "gui/$uid" "$plist"
printf 'Installed %s to run daily at %02d:%02d (Mac local time).\n' "$label" "$hour" "$minute"
printf 'Logs: %s/backup.log and %s/backup-error.log\n' "$logs" "$logs"
printf 'Manual test: launchctl kickstart gui/%s/%s\n' "$uid" "$label"
printf 'To inspect: launchctl print gui/%s/%s\n' "$uid" "$label"
printf 'To disable: launchctl bootout gui/%s %q\n' "$uid" "$plist"
