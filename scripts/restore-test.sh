#!/usr/bin/env bash
# HomeLab Phase 05 — non-destructive restoration verification on Mac host.
# Does NOT overwrite or modify the live storage server.
set -euo pipefail

[[ "$(uname -s)" == 'Darwin' ]] || { echo 'Run this script on macOS.' >&2; exit 1; }
if [[ $# -ne 1 || ! -d "$1" ]]; then
  echo 'Usage: bash scripts/restore-test.sh <backup-directory>' >&2
  exit 2
fi
backup="$1"
archive="$backup/files.tar.gz"
checksum="$backup/files.tar.gz.sha256"
[[ -s "$archive" && -s "$checksum" ]] || { echo 'Backup or checksum missing.' >&2; exit 1; }

(
  cd "$backup"
  shasum -a 256 -c files.tar.gz.sha256
  tar -tzf files.tar.gz > /dev/null
)

scratch="$(mktemp -d "$backup/.restore-test.XXXXXX")"
cleanup() { [[ -d "$scratch" ]] && rm -rf -- "$scratch"; }
trap cleanup EXIT

tar -xzf "$archive" -C "$scratch"
[[ -d "$scratch/files" ]] || { echo 'Missing files/ in restored backup.' >&2; exit 1; }
files="$(find "$scratch/files" -type f | wc -l | tr -d ' ')"
printf 'RESTORE TEST PASSED: archive integrity verified and extracted to an isolated temporary directory.\n'
printf 'Files recovered: %s\n' "$files"
if [[ -f "$scratch/files/sample-transfer.txt" ]]; then
  printf 'Recovered test-file SHA-256: '
  shasum -a 256 "$scratch/files/sample-transfer.txt" | awk '{print $1}'
fi
printf 'Live storage server was not changed.\n'
