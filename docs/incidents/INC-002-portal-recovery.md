# INC-002 — Nginx Portal Recovery Validation

## Objective

Verify that Ansible can recover an intentionally stopped Docker
service without recreating its container or disrupting monitoring.

## Environment

- Host: lab-gw
- Service: homelab-portal-portal-1
- Orchestration: Ansible and Docker Compose
- Playbook: ansible/playbooks/13-manage-compose-services.yml

## Test procedure

1. Recorded the existing portal container ID.
2. Intentionally stopped the portal container.
3. Confirmed that HTTP access to port 8080 failed.
4. Executed the Ansible Compose management playbook.
5. Verified successful service health checks.
6. Compared the container ID before and after recovery.

## Observed results

| Check | Result |
|---|---|
| Outage confirmed | PASS |
| Ansible recovery | PASS |
| Portal HTTP health | PASS |
| Prometheus health | PASS |
| Grafana health | PASS |
| Container ID preserved | PASS |
| Playbook failures | 0 |


Recovery execution:
- Tasks OK: 16
- Tasks changed: 1
- Failed: 0
- Unreachable: 0

## Conclusion

Ansible successfully restored the stopped Nginx portal
while preserving the existing Docker container.

The experiment validates operator-initiated service recovery.
It does not validate automatic failure detection, recovery
from deleted containers, full VM restoration, or physical
disk failure recovery.

See the [evidence index](../../evidence/README.md) for the saved outage, play recap and matching before/after captures.
