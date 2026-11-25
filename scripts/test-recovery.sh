#!/usr/bin/env bash
set -euo pipefail

fail() { printf 'Recovery refused: %s\n' "$*" >&2; exit 2; }

[[ ${RECOVERY_MODE:-} == isolated || ${RECOVERY_MODE:-} == original ]] ||
  fail 'set RECOVERY_MODE=isolated or RECOVERY_MODE=original'
[[ -n ${RECOVERY_INVENTORY:-} && -f $RECOVERY_INVENTORY && -r $RECOVERY_INVENTORY ]] ||
  fail 'set RECOVERY_INVENTORY to an explicit readable inventory file'
[[ ${RECOVERY_TARGET:-} =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]] ||
  fail 'set RECOVERY_TARGET to one inventory host name'
[[ ${RECOVERY_RUN:-} =~ ^[0-9]{8}T[0-9]{6}Z$ ]] ||
  fail 'set RECOVERY_RUN to the UTC monitoring backup run ID'
[[ ${RECOVERY_APPROVED:-} == yes ]] ||
  fail 'set RECOVERY_APPROVED=yes after approving temporary recovery resources'
if [[ $RECOVERY_MODE == original ]]; then
  [[ ${RECOVERY_HOSTNAME:-} == lab-gw && ${RECOVERY_ORIGINAL_APPROVED:-} == lab-gw ]] ||
    fail 'the original gateway requires RECOVERY_HOSTNAME=lab-gw and RECOVERY_ORIGINAL_APPROVED=lab-gw'
else
  [[ ${RECOVERY_HOSTNAME:-} =~ ^homelab-fresh-[a-z0-9][a-z0-9-]*-gw$ ]] ||
    fail 'set RECOVERY_HOSTNAME to the provisioned isolated gateway hostname'
fi

export RECOVERY_RUN RECOVERY_TARGET RECOVERY_HOSTNAME RECOVERY_MODE
export RECOVERY_APPROVED RECOVERY_ORIGINAL_APPROVED
export RECOVERY_BACKUP_ROOT RECOVERY_WINDOW_SECONDS
set --
if [[ ${RECOVERY_ASK_BECOME_PASS:-} == yes ]]; then set -- -K; fi
printf 'Recovery host %s (inventory host %s, mode %s) | archive %s | inventory %s\n' \
  "$RECOVERY_HOSTNAME" "$RECOVERY_TARGET" "$RECOVERY_MODE" "$RECOVERY_RUN" "$RECOVERY_INVENTORY"
exec "${ANSIBLE_PLAYBOOK:-ansible-playbook}" -i "$RECOVERY_INVENTORY" "$@" \
  ansible/playbooks/17-test-prometheus-startup.yml ansible/playbooks/18-test-grafana-startup.yml
