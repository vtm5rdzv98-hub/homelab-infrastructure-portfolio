# Evidence summaries

These results were compiled from the operator's November 23–24, 2026 build records. The raw evidence remains private. Results are specific to the observed runs.

| Exercise | Recorded signal | Private source filename |
| --- | --- | --- |
| Network policy | The gateway and storage network assertions passed. | `phase06-network-policy-verification.txt` |
| Repeat runs | SSH, storage firewall, storage mount, Docker file adoption and Compose repeat runs recorded zero changes and zero failures. | Phase 06 idempotency captures |
| Portal failure and recovery | An HTTP outage was confirmed, Ansible reported one change and no failures, and the before/after container ID captures matched. | `phase06-recovery-*.txt` |
| Exporter failure | All three Prometheus jobs recorded value `1` after setup. NodeDown fired in the controlled outage and the final alert list was empty. | `phase04-three-targets.json` and alert captures |
| Storage backup and sample restore | Successful storage backups were logged. The source and separately restored sample SHA-256 values matched. | `phase05-backup-execution.log`, `phase05-server-restoration.txt` |
| Monitoring archives | `grafana.tar.gz: OK` and `prometheus.tar.gz: OK` for the archive set used in the recovery test. | `phase06-monitoring-backup-20261124T050335Z.txt` |
| Prometheus recovery | The restored instance started, completed WAL replay and reported ready. The existing volume was absent from the test container. | `phase06-prometheus-startup-permissions-fix.txt` |
| Grafana recovery | Grafana 13.3.1 started and its database reported healthy. The test instance had no network or published ports and did not mount the existing volume. | `phase06-grafana-startup-recovery.txt` |

See the [verification matrix](../docs/TEST_PLAN.md) for corresponding runbooks and open tests.

## Published visual evidence

See the [eight authentic screenshots](../docs/EVIDENCE_GALLERY.md): Nginx portal, Grafana dashboard, three UP Prometheus targets, NodeDown baseline/firing/clearing, and two storage capacity queries. See [TEST-004](../docs/tests/TEST-004-engineering-completion.md#fresh-deployment-on-the-mac) for storage interface and routing checks. Screenshots are curated proof of *point-in-time* outcomes; full terminal logs and backup archives remain private.
