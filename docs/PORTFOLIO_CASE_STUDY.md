# HomeLab Infrastructure — Engineering case study

## Project overview

**Role:** Independent infrastructure engineering project · **Environment:** Intel MacBook Pro with 8 GB RAM, VirtualBox and Ubuntu Linux · **Focus:** Linux administration, networking, automation, observability and recovery.

I designed and built a two-node Ubuntu lab to practice operating infrastructure with realistic security and failure constraints on limited hardware. The gateway hosts a containerized Nginx portal and Prometheus/Grafana monitoring; a separate storage VM exposes SFTP and Node Exporter over an isolated VirtualBox network.

The project progressed from manual deployment and management to a repeatable cloud-image bootstrap, defined acceptance tests, and evidence-backed monitoring and recovery experiments.

## Problem and design

I wanted a small system that could demonstrate actual infrastructure skills rather than only displaying a dashboard. The design needed to show controlled access, persistent storage, service operations and failure recovery while remaining viable on an eight-gigabyte Mac.

I chose a gateway/storage split because it let me test **network boundaries and an SSH jump host**: the Mac reaches the gateway through a localhost-bound forwarded port and reaches storage by ProxyJump. Storage has a private-only network interface and a dedicated ext4 data volume. The gateway runs Nginx, Prometheus, Grafana and Node Exporter through Docker Compose; the storage exporter is scraped across the internal network.

## Implementation

- **Linux and access:** Ubuntu Server guests, key-based SSH, SSH hardening, UFW allow rules scoped to needed services and private routing.
- **Configuration as code:** Ansible playbooks for audits, SSH policy, storage mounting, Docker/Compose, service operations and monitoring recovery. Existing-service repeat runs were checked for unintended changes.
- **Fresh provisioning:** A separate VirtualBox, Ubuntu Cloud, cloud-init and guarded Ansible workflow generated two fresh VMs with pinned SSH host keys. The new storage VM was rebooted after temporary NAT removal; its private routing, persistent ext4 mount and SFTP round trip passed. A repeat Ansible bootstrap reported no changes.
- **Observability:** Three Prometheus jobs and a Grafana dashboard for host/service metrics. A controlled storage-exporter interruption produced an actual NodeDown alert transition from inactive to firing and back to inactive after recovery.
- **Reliability:** An intentionally stopped Nginx portal was restored through operator-initiated Ansible without changing the container ID. Storage backups were checksum-verified, and one verified copy was independently stored and test-extracted on the FileVault-encrypted Mac internal disk.
- **Application recovery:** Isolated recovery containers replayed Prometheus WAL and returned four representative archived historical metrics. An isolated Grafana instance passed database health and retrieved the archived dashboard UID and panels through its API. The updated recovery workflow also checked resource isolation and cleanup.

## Verification and measurable acceptance

| Exercise | Recorded result |
| --- | --- |
| Fresh-VM acceptance | **9/9** live checks passed, including SSH jump, ext4 mount, three scrape targets, Grafana, portal and private storage routing |
| Idempotency | Repeated fresh Ansible bootstrap: **0 changes**, **0 failures** on both hosts |
| SFTP | Upload/download content verified byte-for-byte and by SHA-256 |
| Monitoring | A controlled NodeDown rule fired during exporter interruption and cleared after recovery |
| Monitoring restoration | Four historical Prometheus queries returned archived data; restored Grafana dashboard/panels were accessible through API |
| Backup | 20:00 scheduled run observed, verified archive and separate encrypted-disk copy test-extracted |
| Automated repository validation | Local offline suite and GitHub Actions validation passed in the recorded project acceptance |

See [TEST-004](tests/TEST-004-engineering-completion.md), [test matrix](TEST_PLAN.md), and [genuine screenshots](EVIDENCE_GALLERY.md). These represent recorded test runs—not a claim that the services are continuously healthy today.

## Tradeoffs and boundaries

The local system is not high availability: **alert detection is not automatic repair**, and the portal recovery was operator initiated. Recurring independent backups have an implemented workflow but are not scheduled, and full loss of a physical disk has not been rehearsed. Authentication with the original Grafana account in a restored instance and measured RTO/RPO have not been verified.

Those distinctions matter: the project demonstrates practical provisioning, controls, monitoring and recovery testing without claiming production-grade fault tolerance.

## Portfolio-ready summary

**HomeLab Infrastructure — Linux Automation, Observability & Recovery**

Built a reproducible two-node Ubuntu HomeLab using VirtualBox, cloud-init, Ansible and Docker Compose. Segmented SFTP storage behind an SSH jump gateway, secured services with SSH and UFW policies, and monitored three Prometheus targets through Grafana. Validated a fresh deployment with nine live checks and idempotent Ansible, demonstrated real NodeDown alert transitions, and tested checksum-verified backups plus isolated Prometheus/Grafana recovery.

**Technologies:** Ubuntu Linux · VirtualBox · Ansible · Docker Compose · SSH/ProxyJump · UFW · Nginx · SFTP · Prometheus · Grafana · Python · Bash · GitHub Actions

## Demo and evidence

A concise, evidence-based walkthrough is mapped in the [video production guide](DEMO_PRODUCTION_GUIDE.md). The video is not yet recorded. The [README](../README.md) links the source, project architecture and verified documentation.
