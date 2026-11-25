# TEST-004 — Engineering completion verification

The original acceptance runs used the Intel Mac on November 24–25, 2026. On November 25, the follow-up rechecked the original lab and exercised the new recovery guards and replication workflow, followed by a full rerun of the updated recovery target on the isolated gateway. Raw logs, archive contents, host keys, fingerprints, VM UUIDs, and physical paths are kept in private notes. The [evidence gallery](../EVIDENCE_GALLERY.md) preserves the original screenshots.

## Fresh deployment on the Mac

| Step | Reproduce | Observed acceptance |
| --- | --- | --- |
| Provision clean guests | Follow the [fresh deployment guide](../FRESH_DEPLOYMENT.md) using VirtualBox 7.2.22, the Ubuntu 26.04 amd64 cloud image and its published SHA-256. Apply `provision-vbox.py create --apply` with an unused prefix, host port and private network. | Two independent guests booted from new system VDIs. Storage had its own data VDI. |
| Establish SSH trust and isolation | Run `provision-vbox.py trust` and use the generated SSH configuration with `StrictHostKeyChecking yes`. Use that configuration to reach the storage hostname through the gateway. After bootstrap, shut down only test storage, set `VBoxManage modifyvm <fresh-storage> --nic1=none` and restart it. | The controller pinned the two console-emitted host keys. Storage was reachable through the SSH jump. Both IPv4 and IPv6 default-route checks passed after reboot. |
| Bootstrap and verify | Run `ansible-playbook -i <fresh-inventory> -e fresh_deploy=true ansible/playbooks/bootstrap-fresh.yml`. Set the fresh aliases and exporter unit described in the guide and run `make validate-live`. | Both plays completed, the dedicated ext4 volume mounted by UUID after reboot, and all nine checks passed, including three healthy scrape jobs. |
| SFTP integrity | Upload a synthetic sample to a unique name in `/srv/homelab/data/files` with SFTP through the configured jump. Download that file to a different local name, compare with `cmp` and `shasum -a 256`, then remove only the uploaded sample. | `cmp` passed during acceptance. The follow-up recomputed SHA-256 on the retained upload and download fixtures and both digests matched. The uploaded sample was removed. |
| Idempotency | Repeat the same bootstrap against the fresh inventory after removal of storage NAT. | Both hosts reported `changed=0`, `unreachable=0` and `failed=0`. |

Both original VMs passed the nine-check suite after the earlier maintenance window. On November 25, the follow-up ran `make validate-live` again with the original aliases and got nine passes and zero failures. VirtualBox showed only the original two VMs running and both fresh VMs powered off.

## Isolated monitoring recovery on the Mac

1. Stage the two monitoring archives and `SHA256SUMS` from the selected backup on an isolated gateway, and run `shasum -a 256 -c SHA256SUMS` on the staged files. The archived run exercised here was `20261124T050335Z`.
2. Use the isolated mode in the [monitoring recovery runbook](../RUNBOOK.md#select-the-recovery-host-explicitly), selecting the fresh gateway by inventory alias and actual hostname. For the original acceptance, the Mac controller ran the two recovery playbooks on the disposable gateway.
3. Check the application results and cleanup. Each isolated run had a private scratch data bind, no networking or published ports, and no original service volume.

| Application | Observed acceptance |
| --- | --- |
| Prometheus | WAL replay and readiness passed. Four 30-minute historical range queries returned data for the three scrape jobs and storage filesystem availability. |
| Grafana | Version 13.3.1 reported a healthy restored database. The versioned API returned the archived HomeLab dashboard UID and its panels. The archived record contained seven panels. Early attempts without the matching provider returned 404. An empty provider with deletion disabled preserved the archived record without importing a replacement definition. |
| Cleanup | Both containers, their extracted data directories and the staged archive copies were removed from the disposable gateway. |

Grafana used an isolated Viewer. Authentication with the restored account's original credentials remains unverified. Full physical-device-loss recovery and measured recovery objectives remain unverified.

The first follow-up checked the explicit host and pre-start mount gates with fixtures and exercised the new archive guard in private Mac scratch space.

### Final end-to-end run of the updated target

On November 25, the Mac controller ran `make test-recovery` with the isolated mode, a dedicated inventory, explicit target and hostname, and verified copies of run `20261124T050335Z`. The fresh gateway ran with a temporary 1,792 MiB memory allocation while both original VMs stayed online. The fresh storage VM stayed powered off.

| Check | Observed result |
| --- | --- |
| Target and mount gates | Both playbooks accepted the explicit fresh gateway, verified the archive checksums, and checked the exact scratch-only bind mounts and Docker isolation settings before starting the containers. |
| Prometheus | WAL replay and readiness passed. All four historical queries returned archived data. The gateway's baseline Prometheus endpoint remained healthy after cleanup. |
| Grafana | The restored 13.3.1 database was healthy and the API returned the archived dashboard and panels. The gateway's baseline Grafana endpoint remained healthy after cleanup. The test used an isolated Viewer. |
| Cleanup | The target returned exit 0 with zero failed or unreachable hosts. Follow-up checks found zero recovery-labeled containers and zero matching extraction directories. The staged archive copies were removed from the fresh gateway and Mac scratch space. |

After the drill, the fresh gateway shut down cleanly and its 2,560 MiB memory allocation was restored. Both fresh VMs were powered off, and the original lab passed all nine read-only health checks again. The Mac’s free-memory indicator stayed at or above 45% in the samples taken during the drill.

## Storage backup and independent copy

| Check | Observed acceptance |
| --- | --- |
| Calendar firing | macOS recorded `Running StartCalendarInterval` on November 24 at 19:59:59.994 EST. The 20:00 job wrote run `20261125T010002Z`, verified its checksum and logged success at 20:00:03. Last exit code was 0 when inspected. |
| Independent physical device | `diskutil info` identified the external source and the FileVault-encrypted internal destination as different physical devices. `copy-backup.py storage` verified the source and staged destination. `restore-test.sh` extracted two files and verified the sample file digest. See the [one-time copy procedure](../PHASE05-BACKUP-RUNBOOK.md#copy-a-verified-run-to-independent-media). |
| Optional recurring job | On the Mac, a synthetic run across the external and internal disks copied two completed fixtures, deferred one without a manifest and reverified both copies on retry. An intentionally impossible free-space reserve returned a failure, left no published or partial copy for that fixture, suppressed retention preview and preserved both committed copies and sources. Follow the [recurring copy procedure](../PHASE05-BACKUP-RUNBOOK.md#optional-recurring-off-device-copy) with disposable fixture paths to repeat this test. |

Recurring replication remains unconfigured. No off-device LaunchAgent was enabled and no existing backup was deleted.

## Offline validation and GitHub CI

- **Mac controller** ran `make validate` for repository tests, shell syntax, Ansible syntax, Compose configuration and repository-relative Markdown links. The Mac also ran the hardware and service checks above.
- **GitHub-hosted runner** ran only the offline target during the engineering acceptance and passed. The portfolio retains the same workflow in [Offline validation](../../.github/workflows/validate.yml). The Mac controller ran the live VM and backup checks.
