#!/usr/bin/env bash
# Read-only macOS host capability audit. Does not print serial numbers or usernames.
set -euo pipefail
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This audit is intended for the macOS host." >&2
  exit 1
fi
printf '== HomeLab host readiness (read-only) ==\n'
printf 'macOS: %s\n' "$(sw_vers -productVersion)"
printf 'CPU architecture: %s\n' "$(uname -m)"
printf 'Logical CPU count: %s\n' "$(sysctl -n hw.logicalcpu)"
RAM_BYTES="$(sysctl -n hw.memsize)"
awk -v b="$RAM_BYTES" 'BEGIN {printf "Physical RAM: %.1f GiB\n",b/1024/1024/1024}'
printf 'Available disk at current directory: '
df -Pk . | awk 'NR==2 {printf "%.1f GiB\n",$4/1024/1024}'
if command -v VBoxManage >/dev/null 2>&1; then
  printf 'VirtualBox: %s\n' "$(VBoxManage --version)"
else
  printf 'VirtualBox: not found in PATH\n'
fi
printf '\nReview Oracle-supported macOS versions and actual available RAM/disk before installing VMs.\n'
