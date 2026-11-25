# Project status and unresolved work

**Completion audit on November 24–25, 2026.** The historical design gates are retained in the [master plan](../MASTER_PLAN.md).

## Built and verified

| Area | Evidence-supported result |
| --- | --- |
| Two-node topology | Both Ubuntu VirtualBox VMs started and were accessible; gateway SSH from the Mac succeeded. |
| Private network and security | Storage has an internal-only IPv4 path, no default IPv4 route in recorded check, managed UFW rules, SSH key access and jump-host path. |
| Useful services | Nginx service portal, storage SFTP path, Grafana, Prometheus and two Node Exporters deployed. |
| Monitoring | Three targets UP in Prometheus; Grafana dashboard displayed; controlled NodeDown alert fired and cleared. |
| IaC | Ansible playbooks passed syntax; managed config and Compose repeat runs exhibited no changes; monitoring recovery playbooks executed. |
| Failure drill | Stopped portal was restored with Ansible and same Docker container ID. This was operator-initiated recovery, not automatic failover. |
| Data restoration | Sample storage file hash matched after isolated restoration; monitoring archives passed checksum checks. |
| Application recovery | Isolated Prometheus started and replayed WAL; isolated Grafana started and reported database healthy; production health rechecked. |
| Original lab health | All nine expanded smoke checks passed before maintenance and again after the original VMs restarted. |
| Storage backup LaunchAgent | The 20:00 EST calendar event fired on November 24 and completed with a verified archive and exit code 0. |
| Independent storage recovery | One storage backup passed verification and isolated extraction from the FileVault-encrypted internal disk. |

## Completion workflows

| Area | Scope |
| --- | --- |
| Fresh deployment | [VirtualBox and cloud-init](FRESH_DEPLOYMENT.md) reproduced the lab on a new pair. Storage rebooted without NAT, the mount and SFTP passed, and the repeated play reported zero changes on both guests. |
| Recovery depth | `make test-recovery` runs isolated applications and retrieved historical Prometheus samples and the archived Grafana dashboard through its API. The optional test with restored account credentials remains unverified. |
| Validation | `make validate` covers offline checks. `make validate-live` checks service endpoints, all three scrape jobs, and storage routing. |
| Demo | The [timed narration and screen sequence](DEMO_OUTLINE.md) is ready to record. |

The [completion evidence](tests/TEST-004-engineering-completion.md) records actual execution and test limits.

## Remaining limits

- The optional recurring independent-copy workflow passed a cross-device fixture test and remains unconfigured. The existing 20:00 job writes to the external SSD that holds the VMs. Full physical-device-loss recovery remains unverified.
- Fully automatic repair is outside this design. The portal exercise used an operator-initiated Ansible repair.
- Recovery time and recovery point objectives have yet to be measured.
- The narrated demo awaits recording.
