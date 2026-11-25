#!/usr/bin/env bash
# Read-only smoke checks from the Mac using the configured lab SSH aliases.
set -u

failures=0
gateway=${HOMELAB_GATEWAY_SSH:-homelab}
storage=${HOMELAB_STORAGE_SSH:-homelab-storage}
exporter_unit=${HOMELAB_STORAGE_EXPORTER_UNIT:-node-exporter}
ssh_options=(-o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=5)
if [[ -n "${HOMELAB_SSH_CONFIG:-}" ]]; then
  ssh_options+=(-F "$HOMELAB_SSH_CONFIG")
fi

check() {
  local label="$1"
  shift
  printf '[TEST] %s ... ' "$label"
  if "$@" >/dev/null; then
    printf 'PASS\n'
  else
    printf 'FAIL\n'
    failures=$((failures + 1))
  fi
}

check 'Gateway SSH' ssh "${ssh_options[@]}" "$gateway" true
check 'Storage SSH via jump host' ssh "${ssh_options[@]}" "$storage" true
check 'Storage data mount' ssh "${ssh_options[@]}" "$storage" \
  'findmnt --mountpoint /srv/homelab/data --noheadings --output FSTYPE | grep -qx ext4 && test -d /srv/homelab/data/files'
check 'Storage Node Exporter service' ssh "${ssh_options[@]}" "$storage" systemctl is-active "$exporter_unit"
check 'Portal HTTP' ssh "${ssh_options[@]}" "$gateway" \
  'curl --max-time 8 -fsS http://127.0.0.1:8080/'
check 'Prometheus readiness' ssh "${ssh_options[@]}" "$gateway" \
  'curl --max-time 8 -fsS http://127.0.0.1:9090/-/ready'
check 'Three expected Prometheus scrape jobs' ssh "${ssh_options[@]}" "$gateway" \
  'set -e; targets=$(curl --max-time 8 -fsS http://127.0.0.1:9090/api/v1/targets); printf "%s" "$targets" | python3 -c "
import json, sys
payload = json.load(sys.stdin)
expected = {\"prometheus\", \"lab-gw\", \"lab-storage\"}
targets = payload[\"data\"][\"activeTargets\"]
for job in sorted(expected):
    matching = [t for t in targets if t[\"labels\"].get(\"job\") == job]
    if len(matching) != 1 or matching[0][\"health\"] != \"up\":
        sys.exit(f\"Expected exactly one healthy target for {job}\")
"'
check 'Storage has no IPv4 or IPv6 default route' ssh "${ssh_options[@]}" "$storage" \
  'set -e; v4=$(ip -4 route show default); v6=$(ip -6 route show default); test -z "$v4$v6"'
check 'Grafana database health' ssh "${ssh_options[@]}" "$gateway" \
  'set -e; health=$(curl --max-time 8 -fsS http://127.0.0.1:3000/api/health); printf "%s" "$health" | python3 -c "import json, sys; sys.exit(json.load(sys.stdin).get(\"database\") != \"ok\")"'

printf '\n%d failed checks.\n' "$failures"
test "$failures" -eq 0
