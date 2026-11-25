# Security model

| Boundary | Control and verification |
| --- | --- |
| Mac to gateway | VirtualBox forwards SSH on Mac loopback. SSH uses keys and rejects root and password logins per the saved SSH audit. Verify host fingerprints through the console. |
| Gateway to storage | A VirtualBox internal network carries SSH/SFTP and metrics. Storage has no IPv4 default route. Recorded UFW rules allowed TCP 22 and 9100 only from the gateway's private IP. |
| Mac to web UIs | Nginx, Prometheus and Grafana publish on gateway loopback. Operators use SSH tunnels. Check actual listeners alongside UFW when changing Docker ports. |
| Grafana and monitoring | Grafana's initial password is file-backed and provisioned outside Git. Its persistent database and backups may contain user or application data. Node Exporter's host namespace and filesystem access are part of the trusted gateway stack. |
| Backups | Backups use SSH and checksums. Keep manifests with trusted archives and restrict access to archive directories. The scheduled copy shares the VMs' external SSD. One storage backup was verified and restored from the FileVault-protected internal disk. |

The lab assumes a trusted Mac host, VirtualBox management plane and gateway operator. Exposure from a compromised gateway, actual recurring off-device copies and complete device-loss recovery are outside the demonstrated scope.

The fresh-VM workflow pins guest-generated host keys from private VirtualBox serial logs, and only the gateway presents a localhost-bound SSH port. For recovery tests, Grafana dashboard access stays inside the disposable container namespace.

Before publishing, review the full staged diff and the commit metadata for credentials, personal paths, host identity, private inventory, backup artifacts and raw command output. The repository includes only curated evidence summaries. Private RFC 1918 addresses shown in documentation describe the isolated reference topology.
