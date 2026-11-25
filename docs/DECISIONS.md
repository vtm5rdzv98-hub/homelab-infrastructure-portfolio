# Architecture Decision Records

ADRs 001–006 reflect the initial design. The deployed topology is documented in the [architecture](ARCHITECTURE.md).
## ADR-001 — Start with one VM, expand to two

**Status:** Accepted for design; validate against real host resource data.
**Context:** 2018 MacBook Pro, 8 GiB physical memory and constrained free storage.
**Decision:** Start with CLI-only gateway; provision storage only after the first milestone and measured capacity.
**Consequences:** Lower risk of swap and unusable host; distributed-node features arrive later. The second VM may need to be shut down outside testing.

## ADR-002 — VirtualBox and Ubuntu 24.04 LTS

**Status:** Conditional on host OS version.
**Decision:** Oracle VirtualBox on a supported Intel macOS release, Ubuntu Server 24.04 LTS guests.
**Consequences:** Easy-to-reproduce virtualization; installer compatibility must be confirmed in Phase 00. Avoid unsupported installer/kernel configurations.

## ADR-003 — Host-only + internal network, plus NAT for updates

**Status:** Proposed.
**Decision:** Mac reaches gateway through a host-only interface; storage reachable only on a separate internal VM network through SSH ProxyJump; guest NAT adapters retained for updates.
**Consequences:** Demonstrates access control without buying networking hardware; not truly air-gapped and NAT does not imply zero outbound risk.

## ADR-004 — Lightweight service before dashboards

**Status:** Proposed.
**Decision:** Static Caddy service portal + OpenSSH SFTP service, with Prometheus/Grafana only after working core.
**Consequences:** The first functional milestone has low overhead; monitoring is still a full-stack capstone once memory measurements permit it.

## ADR-005 — No public exposure

**Status:** Accepted.
**Decision:** No inbound router changes, public DNS, port forwarding, or bridged VM NICs.
**Consequences:** Easier to secure and reproduce locally; demo must be recorded instead of linking to a live internet service.

## ADR-006 — Real measurement, not illustrative metrics

**Status:** Accepted.
**Decision:** Keep dashboards empty until working exporters; use actual capture logs, real failure timings and actual screenshots.
**Consequences:** More work, but defendable project results.

## ADR-007 — Predictable Docker bridge for firewall scoping

**Status:** Proposed, verify no subnet collision.
**Decision:** Reserve `172.30.77.0/24` for Compose containers; gateway allows node-exporter scrapes from this subnet only.
**Consequences:** UFW rule can be specific; requires a pre-deployment conflict check and careful adjustment if it overlaps local/VPN networks.

## ADR-008 — Keep lab web services on loopback

Nginx, Prometheus and Grafana bind their published ports to gateway loopback. The Mac uses SSH tunnels and reaches storage through a jump host. The gateway retained NAT for updates, and storage uses the internal network without a default route.

## ADR-009 — Recover from isolated archive copies

Restore checks extract into temporary directories and mount those copies into isolated containers. This exercises startup and database readiness with minimal risk to the existing monitoring volumes. The next recovery boundary is a clean VM or replacement disk with independently stored backups.
