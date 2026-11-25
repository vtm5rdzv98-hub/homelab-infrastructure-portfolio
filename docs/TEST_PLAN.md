# Verification matrix

The observed outcomes below come from the private build records. The [evidence index](../evidence/README.md) summarizes those records. Record a fresh timestamp and scope when rerunning a check.

| Test | Observed result | Reproduction entry point |
| --- | --- | --- |
| SSH and network isolation | SSH hardening and both host paths verified. Storage default route absent in the Phase 06 check and firewall policy restricted to gateway access. | Ansible `03`, `05`, `06` and the smoke script |
| Persistent storage | ext4 mount verified and mount playbook repeat run reported zero changes. Sample file checksum matched after restoration to a separate storage path. | Ansible `08`, `09` and [storage backup runbook](PHASE05-BACKUP-RUNBOOK.md) |
| Portal and monitoring | Portal recovered with container ID preserved. Compose repeat run reported zero changes. All three Prometheus jobs recorded up. | [INC-002](incidents/INC-002-portal-recovery.md) and Ansible `13` |
| Exporter failure detection | NodeDown fired in Prometheus and cleared after exporter recovery. | [INC-001](incidents/INC-001-node-exporter-outage.md) |
| Monitoring archive integrity | Both archives passed SHA-256 verification. Restored Grafana database passed SQLite integrity check. | [TEST-002](tests/TEST-002-monitoring-data-restore.md) |
| Monitoring application startup | Prometheus WAL replay and readiness passed. Grafana startup and database health passed. Both production endpoint checks passed after the isolated tests. | [TEST-003](tests/TEST-003-monitoring-application-recovery.md) |
| Monitoring recovery depth | Four historical Prometheus queries returned data. Restored Grafana served the archived dashboard UID and panels through its API. Restored account credentials were not exercised. | `make test-recovery` and [TEST-004](tests/TEST-004-engineering-completion.md) |
| Fresh bootstrap and storage reboot | The fresh pair bootstrapped from Ubuntu Cloud. Storage rebooted with NAT removed, mounted ext4, and passed a byte-for-byte SFTP round trip. All nine live checks passed. | [Fresh deployment](FRESH_DEPLOYMENT.md) and [TEST-004](tests/TEST-004-engineering-completion.md) |
| Calendar backup and independent storage copy | The 20:00 calendar job ran. The copy passed SHA-256 checks and isolated extraction from a separate encrypted physical disk. | [Backup runbook](PHASE05-BACKUP-RUNBOOK.md) and [TEST-004](tests/TEST-004-engineering-completion.md) |
| Full physical device-loss recovery | Unverified. One independent storage copy was exercised. Recovery-time and recovery-point objectives remain unmeasured. | Requires a separate recovery environment and independent copies of VM and monitoring assets. |

Current health is a separate observation. Run the read-only smoke check in the [runbook](RUNBOOK.md) when both VMs are available.
