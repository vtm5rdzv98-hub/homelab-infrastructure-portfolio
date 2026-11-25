# TEST-003 — Monitoring Application Recovery

## Objective

Validate that Grafana and Prometheus can start successfully
from archived monitoring data using isolated application instances.

## Environment

- Host: lab-gw
- Container runtime: Docker
- Automation: Ansible
- Grafana: 13.3.1
- Prometheus: 3.16.0
- Backup ID: 20261124T050335Z

## Test methodology

Both archives were extracted into temporary directories on the
gateway.

Temporary Docker containers were started using the restored
data rather than the production Docker volumes.

External container networking was disabled, and no test
ports were published.

Ansible performed health verification and removed temporary
resources after testing.

## Prometheus results

| Check | Result |
|---|---|
| Archived TSDB opened | PASS |
| TSDB blocks inspected | PASS |
| Application startup | PASS |
| WAL replay | PASS |
| Readiness verification | PASS |
| Production instance health | PASS |
| Temporary resource cleanup | PASS |

Execution recap:
- OK: 21
- Changed: 6
- Failed: 0

## Grafana results

| Check | Result |
|---|---|
| Restored SQLite database available | PASS |
| Application startup | PASS |
| Database health | PASS |
| Version verification | PASS |
| Isolated data mount | PASS |
| Production instance health | PASS |
| Temporary resource cleanup | PASS |

Execution recap:
- OK: 23
- Changed: 6
- Failed: 0

Grafana required multiple health-check retries during startup
before reporting a healthy database.

## Limitations

These tests validate application startup and database readiness
using restored monitoring data.

They do not establish:
- Full dashboard functionality or restored user login
- Historical PromQL query correctness
- Alert notification delivery after restoration
- Recovery-time or recovery-point objectives
- Full VM or host replacement
- Recovery from physical loss of the external SSD

The tests ran on the existing gateway with its Docker runtime
and container images already installed.

## Conclusion

Both monitoring applications successfully started using
independently restored backup data.

Prometheus completed WAL replay and reached readiness.
Grafana initialized its restored database and reported healthy.

The production endpoint checks passed after each restore test, and temporary test resources were cleaned up.

See the [evidence index](../../evidence/README.md) for the private startup records and the [runbook](../RUNBOOK.md#back-up-and-test-monitoring-recovery) for playbooks 16–18 and their prerequisites. The current playbooks require an explicit backup ID and verify the archive manifest before restoring. These additional checks were validated locally. The isolated VM recovery results above are from the prior playbook revision.
