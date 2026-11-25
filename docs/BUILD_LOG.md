# Engineering Build Log

This journal separates **intent**, **observations**, **changes**, and **verified results**. Add dates only when work actually happens.

## Entry template (copy when starting a work session)

### YYYY-MM-DD — Phase XX: short task name

**Objective:** What capability should exist at the end?

**Starting state:** What was already working? Include commit ID if applicable.

**Actions:** Concise commands / configuration changes made, with relevant file links.

**Observations:** Expected behavior, actual behavior, resource usage, relevant logs.

**Problems and root cause:** What failed, hypotheses tested, and why the resolution worked.

**Verification:** Test ID(s), result (PASS/FAIL), and evidence path.

**Decision / next action:** Accepted tradeoff, blocker, or next verification step.

---

## 2026-11-22 — Design baseline

**Objective:** Produce a bounded technical project and documentation skeleton.

**Actions:** Defined target architecture, staged memory plan, network access matrix, security constraints, validation matrix, and starter service configuration.

**Observations:** Source code and documents were generated; VMs have not been created or measured.

**Verification:** Local repository static checks may pass, but no deployed-service test has been executed. Do not mark environment tests PASS yet.

**Next action:** Run `scripts/host_audit.sh` on the actual Mac and record the GO/NO-GO decision.

## November 2026 — Implementation and recovery exercises

Deployed the two-node VirtualBox lab and adopted the existing service, security, storage and Compose state in Ansible. The controlled portal outage and isolated monitoring restore exercises are documented in the [verification matrix](TEST_PLAN.md).

## November 2026 — Repository preparation

Updated setup and operations documentation to match the Nginx deployment. Preserved the Caddy example as a historical prototype. Reconciled the evidence with the recovery reports and kept raw captures out of the publishable source. Live SSH checks from the repository preparation environment were blocked.
