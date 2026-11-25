# Portfolio demo production guide

**Target:** 105 seconds · 1920 × 1080 · 30 fps · quiet narration with real UI and evidence · no fabricated monitoring states.

This is a production guide, not a claim that a recording has been completed. Refer to the [existing timed narration](DEMO_OUTLINE.md) for the factual basis and the [evidence gallery](EVIDENCE_GALLERY.md) for existing genuine screenshots.

## Shot list and concise narration

| Timestamp | Visual | Suggested narration |
| --- | --- | --- |
| 00:00–00:15 | Architecture diagram from [ARCHITECTURE](ARCHITECTURE.md); highlight Mac, gateway, storage and SSD | “I built a two-node Ubuntu infrastructure lab on an eight-gigabyte Intel Mac. I isolated the storage guest behind a gateway and used SSH forwarding for management.” |
| 00:15–00:32 | Original portal capture and read-only nine-check command/output (capture a new result only if actually run) | “The gateway serves an Nginx portal. A read-only validation suite checks SSH access, the storage mount, private routing, and monitoring services.” |
| 00:32–00:49 | Prometheus targets UP, Grafana dashboard screenshots | “Prometheus monitors the gateway, storage host and itself. Grafana visualizes utilization and filesystem health across the lab.” |
| 00:49–01:04 | Genuine NodeDown firing and cleared captures | “I intentionally interrupted the storage exporter. The NodeDown alert fired and cleared when I restored the service. This verifies detection—not automatic repair.” |
| 01:04–01:25 | GitHub evidence reports, TEST-004 and fresh deployment guide; optionally a genuine SFTP checksum test capture | “Ansible manages the infrastructure. I independently bootstrapped a fresh pair of virtual machines, verified storage isolation and SFTP, and confirmed a repeat deployment made no changes.” |
| 01:25–01:45 | Backup and isolated recovery report, perhaps split with Grafana screenshot | “I verified scheduled storage backups and a copy on a separate encrypted disk. Isolated restore tests recovered Prometheus historical metrics and the archived Grafana dashboard.” |

## Recording checklist

- [ ] Use genuine, locally captured windows or the supplied screenshots; **do not recreate fabricated terminal results or alerts**.
- [ ] Set display to 1080p or use a stable screen capture canvas; enlarge text so console output can be read at normal playback size.
- [ ] Use a smooth sequence: topology → operation → monitoring → controlled incident → fresh automation → backup and recovery.
- [ ] Show exactly what was demonstrated; use the written test report for validations not available as on-screen footage.
- [ ] Hide or redact SSH private keys, credentials, tokens, device serial numbers, host fingerprints, personal directories and private backup filenames. A screenshot's presence in a private repository is not proof it is safe for publication.
- [ ] Keep timestamps if claiming contemporaneous evidence and add an on-screen note when older archived screenshots appear.
- [ ] Record narration as a single clean take and synchronize screen captures to the factual script; avoid stock space/server visuals or flashy transitions.
- [ ] End on the repository README and documentation. Do not claim HA, automated failover, end-to-end SSD disaster recovery or public availability.
- [ ] Review the complete export once, with audio, at normal speed before posting.

## Deliverables to make outside this repository

- `homelab-demo-1080p.mp4` — final short demonstration, recorded locally.
- Optional private project footage and editable timeline in your portfolio asset folder; no raw console logs or secrets in Git.
- A link to the published demo on the portfolio page and LinkedIn after privacy review.

## Social / portfolio copy

**Project title:** HomeLab Infrastructure — Linux Automation, Observability & Recovery

**One-line summary:** Reproducible two-node Ubuntu infrastructure lab with isolated storage, Ansible and Docker Compose, live Prometheus/Grafana monitoring, and evidence-backed backup and recovery testing.

**Technical contributions:** Provisioned and secured two Ubuntu VMs; implemented SSH jump-host access and private routing; codified service management with Ansible; configured Prometheus and Grafana; tested alert firing, service restoration and archived monitoring data; verified a fresh deployment and one independent backup copy.

**Important limitations:** Recurring independent copies are not enabled; original Grafana credentials and a full physical-device-loss restore were not tested. The response to detected failures is manual.
