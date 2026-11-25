#!/usr/bin/env bash
# HomeLab Phase 05 — verified file-level backup, run on the Mac host.
# Reads only /srv/homelab/data/files from lab-storage through the SSH jump host.
set -euo pipefail

SOURCE_HOST="${HOMELAB_SOURCE_HOST:-homelab-storage}"
VOLUME="${HOMELAB_VOLUME:-}"
SOURCE_DIRECTORY='/srv/homelab/data'
BACKUP_ROOT="$VOLUME/HomeLab/Backups/lab-storage"

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[[ "$(uname -s)" == 'Darwin' ]] || fail 'Run this script from macOS, not inside Ubuntu.'
[[ -n "$VOLUME" ]] || fail 'Set HOMELAB_VOLUME to the external SSD mount path.'
[[ -d "$VOLUME" ]] || fail "SSD not found at $VOLUME"
# Avoid silently writing backup data to the Mac's internal disk if the SSD is disconnected.
mount | grep -F " on $VOLUME (" > /dev/null || fail "SSD is not mounted at $VOLUME"
[[ -d "$VOLUME/HomeLab" ]] || fail 'HomeLab folder not found on SSD; verify the drive path.'
for cmd in ssh tar gzip shasum mktemp; do command -v "$cmd" >/dev/null || fail "Missing $cmd"; done

# Explicitly require noninteractive SSH authentication for a future scheduled job.
ssh -o BatchMode=yes -o ConnectTimeout=15 "$SOURCE_HOST" \
  'test -d /srv/homelab/data/files && test -r /srv/homelab/data/files' \
  || fail "Cannot access source folder using noninteractive SSH. Load the key configured for the SSH alias and retry."

mkdir -p "$BACKUP_ROOT"
stamp="$(date -u '+%Y%m%dT%H%M%SZ')"
work="$(mktemp -d "$BACKUP_ROOT/.partial-${stamp}.XXXXXX")"
cleanup() { if [[ -n "${work:-}" && -d "$work" ]]; then rm -rf -- "$work"; fi; }
trap cleanup EXIT

printf 'Backing up %s:%s/files over SSH...\n' "$SOURCE_HOST" "$SOURCE_DIRECTORY"
ssh -o BatchMode=yes "$SOURCE_HOST" \
  "tar -C $SOURCE_DIRECTORY -cf - files" | gzip -c > "$work/files.tar.gz"

(
  cd "$work"
  tar -tzf files.tar.gz > file-list.txt
  shasum -a 256 files.tar.gz > files.tar.gz.sha256
  shasum -a 256 -c files.tar.gz.sha256
)

printf 'Source: %s:%s/files\nCreated UTC: %s\nType: file-level .tar.gz\nConsistency: best effort; avoid writes during backup\n' \
  "$SOURCE_HOST" "$SOURCE_DIRECTORY" "$stamp" > "$work/backup-info.txt"

final="$BACKUP_ROOT/$stamp"
[[ ! -e "$final" ]] || fail "Backup destination already exists: $final"
mv "$work" "$final"
work=''
printf '\nBACKUP VERIFIED: %s\n' "$final"
printf 'Archive size: '
du -h "$final/files.tar.gz" | awk '{print $1}'
printf 'Restore-test command:\n  bash scripts/restore-test.sh "%s"\n' "$final"
