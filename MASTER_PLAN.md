# HomeLab Infrastructure — Master Plan

**Version:** 0.1 / design baseline — 2026-11-22
**Project objective:** Design, implement, operate, test, and document a small private infrastructure environment that demonstrates Linux administration, network isolation, containerized delivery, observability, security, automation, and recoverability.

> **Historical design baseline:** The `NOT STARTED` entries below record the *original* plan, not the current project state. For actual outcomes and remaining work, see [PROJECT_STATUS](docs/PROJECT_STATUS.md) and the [verification matrix](docs/TEST_PLAN.md).

## Original definition of done

The project is complete only after all of the following have *actually* happened and supporting evidence is saved:

1. Two Ubuntu virtual servers can be reproducibly deployed or clearly documented for manual reproduction.
2. Gateway is reachable from the Mac on the management network; storage is reachable by SSH jump through the gateway but is not directly reachable from the Mac.
3. Gateway serves a real local portal; storage accepts uploads/downloads using SFTP.
4. Monitoring shows current metrics from **both** VMs when the optional monitoring stack is running.
5. SSH key authentication, firewall policies, and correctly scoped container bindings are tested.
6. A file is changed, backed up, intentionally removed, and recovered; checksums match.
7. At least one controlled failure/restart experiment has an outcome and measured recovery time.
8. A fresh setup from written instructions is tested, and any gaps are fixed.
9. README, architecture, decisions, screenshots, troubleshooting notes, and a demo video are finished.
10. The portfolio writeup distinguishes actual results from lab-only constraints and future ideas.

## Phase plan and gates

| Phase | Build work | Acceptance gate | Evidence required | Status |
| --- | --- | --- | --- | --- |
| 00 — Host audit | Inspect OS, CPU architecture, memory, available storage, hypervisor compatibility | Viable virtualization option identified and host resource budget approved | Redacted audit output, choice recorded | NOT STARTED |
| 01 — Linux gateway | Create `lab-gw`; Ubuntu install; SSH keys; baseline packages | Successful SSH access, reboot and system information commands | Terminal capture, VM configuration | NOT STARTED |
| 02 — Segmented networking | Configure host-only/internal networks and `lab-storage`; firewall rules | Approved paths connect; prohibited direct paths do not | IP route/firewall state, connectivity matrix | NOT STARTED |
| 03 — Useful services | Deploy portal via Compose; configure SFTP with sample data | Portal GET succeeds; SFTP upload/download hash matches | Compose status, screenshots, file hash | NOT STARTED |
| 04 — Observability | Install exporters; deploy Prometheus/Grafana via opt-in Compose profile | Both targets UP; live CPU/RAM/disk metrics visible | Target status, dashboard image, resource measurements | NOT STARTED |
| 05 — Automation & backup | Scripts, Ansible, repeatability, host backup and restore | Repeatable config; backup + restored data identical | Command log, checksums, backup manifest | NOT STARTED |
| 06 — Validation | Threat model checks, failure drills, performance snapshots | Test matrix recorded honestly, failures remediated or explained | Redacted results, resource table, incident note | NOT STARTED |
| 07 — Publication | Clean repository, diagrams, portfolio, short narrated demo | Third party can understand/reproduce; no secrets | Public release checklist + final case study | NOT STARTED |

**Status discipline:** `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, or `PASSED` only. These are the original planned gates.

## Minimum viable system (build this first)

- One gateway VM, CLI-based Ubuntu, reachable through SSH.
- Private host-only network; no public port forwarding.
- Docker Compose serving an actual static portal.
- Basic repeatable checks and documentation.

**Expansion gate:** Add the second VM only if the host remains usable and sufficient free RAM/disk exists. Add Grafana only if monitoring does not cause excessive memory pressure or swapping. Resource measurements are a result of the project, not an embarrassment to hide.

## Explicit non-goals

- No public cloud hosting, internet-facing services, expensive hardware, home-router reconfiguration, domain purchases, or public IP requirement.
- No Kubernetes, high availability, multi-region architecture, or enterprise scalability claims.
- No fabricated pentest, uptime, benchmark, or incident data.
- No real personal files while testing recovery; use throwaway samples.

## Engineering threads

**Linux:** users/groups, package management, systemd, service logs, disk and CPU inspection.
**Networking:** three distinct VM networking modes, routing inspection, SSH jump, firewall policy and negative tests.
**Delivery:** container image/configuration control, volumes, restart behavior, service checks.
**Security:** least exposure, key-only SSH after verification, secrets management, patch process.
**Operations:** metrics, troubleshooting, event timeline, routine operation.
**Reliability:** repeatable backup, checksum verification, restore runbook, controlled fault injection.

## Final outputs

- A working, locally reproducible lab and all reproducible non-secret infrastructure files.
- GitHub README with architecture diagram, deployment guide, evidence, measured results, known limitations, and clearly explained tradeoffs.
- Screenshots: topology, portal, Grafana, SSH/SFTP verification, recovery exercise.
- One short demo walkthrough (screen recording with narration): architecture, use case, metrics, segmentation, recovery.
- One polished portfolio page using `docs/PORTFOLIO_CASE_STUDY.md` as the factual basis.

## Decision principles

1. Correctness before appearance. 2. A smaller working system beats a broader incomplete system. 3. Automate only once the manual process is understood. 4. Test what is disallowed, not only what is allowed. 5. Never optimize away the host's stability. 6. Record every meaningful design change.
