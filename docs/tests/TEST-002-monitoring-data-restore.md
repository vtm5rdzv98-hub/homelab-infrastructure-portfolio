# TEST-002 — Monitoring Data Restore Validation

## Objective

Verify that the Grafana and Prometheus monitoring archives
can be transferred, integrity-checked, extracted, and inspected
without modifying the production containers or Docker volumes.

## Backup identifier

20261124T050335Z

## Procedure

1. Created cold backups of Grafana and Prometheus.
2. Transferred both archives to the external SSD.
3. Verified SHA-256 checksums.
4. Extracted both archives into separate restore-test directories.
5. Executed SQLite PRAGMA integrity_check on Grafana's database.
6. Inspected the restored Prometheus TSDB directory structure.

## Results

| Verification | Result |
|---|---|
| Grafana archive SHA-256 | PASS |
| Prometheus archive SHA-256 | PASS |
| Grafana archive extraction | PASS |
| Prometheus archive extraction | PASS |
| Grafana SQLite integrity | PASS |
| Prometheus WAL directory | Present |
| Prometheus TSDB block directories | 2 |
| Production volumes modified | No |

Restored Grafana directory: 382 MB
Restored Prometheus directory: 14 MB

## Limitations

- Application-level recovery has since been validated.
  See [TEST-003](TEST-003-monitoring-application-recovery.md).
- Full VM reconstruction remains untested.
- The backup and VM storage currently share one physical SSD.
- Recovery from complete VM or disk loss remains untested.

## Conclusion

Both monitoring archives passed checksum verification and
non-destructive data restoration checks.

This test validates data-level recovery readiness, not
complete application or VM disaster recovery.

See the [evidence index](../../evidence/README.md) for the archive verification record.
