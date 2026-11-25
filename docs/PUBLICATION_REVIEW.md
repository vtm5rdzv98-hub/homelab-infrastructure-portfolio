# Portfolio publication review

This portfolio uses a reviewed file export with a new Git root. The engineering lab's private history and raw evidence remain private.

## Evidence included

- Eight genuine captures show the portal, Grafana, Prometheus targets, three NodeDown states and two storage capacity queries. The [evidence gallery](EVIDENCE_GALLERY.md) identifies the browser crops and the labeled tooltip redaction.
- The older storage-network capture showed temporary NAT during provisioning. The written [final-state acceptance record](tests/TEST-004-engineering-completion.md#fresh-deployment-on-the-mac) records the SSH jump and default-route checks.
- The documented RFC 1918 topology, SSH architecture, service bindings and engineering configuration are approved for the portfolio. Raw logs, original screenshot files, private Git history, VM disks, backups and credentials stay outside the portfolio.

## Verification before release

- Check the exact release commit with the [release checklist](RELEASE_CHECKLIST.md), including offline CI, repository-relative links, evidence rendering and a secrets scan.
- Review any new screenshots or video for unrelated browser chrome, credentials, host fingerprints, personal paths or raw diagnostics. See the [demo production guide](DEMO_PRODUCTION_GUIDE.md).
- Verify that the author and committer use the approved public attribution. Obtain the owner's approval before making the portfolio repository public.

## Engineering scope

The lab demonstrated a fresh two-node build, repeat Ansible runs, live health checks, a controlled NodeDown event, portal recovery, archived Prometheus history, Grafana dashboard recovery and one verified independent backup copy. See the [test matrix](TEST_PLAN.md) and [project status](PROJECT_STATUS.md).

Recurring independent copies remain unscheduled. A full physical-device-loss restore, restored Grafana login with the original credentials, and measured recovery objectives remain unverified. Alert detection and manual recovery are the tested operating model.
