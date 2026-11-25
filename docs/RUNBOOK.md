# Operations runbook

## Health checks and web access

Run `make validate-live` on the Mac. It checks both SSH paths, the storage mount, exporter and routing, the portal HTTP response, Prometheus readiness and all three scrape jobs, and Grafana's database status.

```bash
ssh -N -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:8080:127.0.0.1:8080 \
  -L 127.0.0.1:9090:127.0.0.1:9090 \
  -L 127.0.0.1:3000:127.0.0.1:3000 homelab
```

Open [Portal](http://127.0.0.1:8080/), [Prometheus](http://127.0.0.1:9090/), or [Grafana](http://127.0.0.1:3000/). Query `up` in Prometheus and look for the `prometheus`, `lab-gw` and `lab-storage` jobs. For storage scrape failures, check the storage exporter service, internal routing and UFW from the gateway. For service failures on the gateway, run `docker compose ps --all` with sudo from the appropriate deployment directory. Use all three Compose files for monitoring.

## Recover the existing portal

With the controller environment active, use the following from the Mac. The playbook imports guarded source adoption and expects the existing portal and all three monitoring containers. It asks Compose to use existing containers without pulling or recreating and compares container IDs afterward. The command can start stopped services. Capture health again after it succeeds. If the container inventory or source checks fail, investigate before applying changes.

```bash
ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/13-manage-compose-services.yml --ask-become-pass
bash scripts/verify-lab.sh
```

Use a maintenance window for intentionally stopping any service. The [portal exercise](incidents/INC-002-portal-recovery.md) records the observed operator-initiated recovery.

## Back up and validate storage data

See the [file backup runbook](PHASE05-BACKUP-RUNBOOK.md) and [LaunchAgent setup](PHASE05-SCHEDULING.md). The Mac pulls only the storage files directory over SSH and validates its archive. The restore script temporarily extracts on the backup disk and leaves the live storage server alone.

## Back up and test monitoring recovery

Use a maintenance window. Playbook `15` briefly stops Grafana and Prometheus in sequence for consistent volume archives, restarts them, checks their endpoints, and generates a checksum manifest. Run one monitoring backup or recovery workflow at a time. Keep a backup copy on separate media if you need to recover from SSD failure.

```bash
run_id="$(date -u +%Y%m%dT%H%M%SZ)"
ansible-playbook -i ansible/inventory/hosts.ini \
  ansible/playbooks/15-backup-monitoring.yml -e "backup_run_id=$run_id" --ask-become-pass
```

After a successful run, copy `grafana.tar.gz`, `prometheus.tar.gz` and `SHA256SUMS` from `~/homelab-monitoring-backups/<run-id>/` on the gateway to a private backup directory with `scp`. Verify the copied archives from that directory with `shasum -a 256 -c SHA256SUMS`. On the gateway check both services after any interrupted run before attempting another backup.

### Select the recovery host explicitly

Stage a trusted archive set on a dedicated fresh gateway. Set `RECOVERY_BACKUP_ROOT` if the archive parent differs from the default `/home/labadmin/homelab-monitoring-backups`. The selected VM needs Python with the tar data filter, Docker with the matching local images, `nsenter` and free scratch space under `/var/tmp`. The command prints the inventory, selected alias, expected VM hostname and archive ID. Before privileged work it verifies that the inventory selects exactly one host and that the host reports the expected hostname.

```bash
make test-recovery RECOVERY_MODE=isolated RECOVERY_APPROVED=yes \
  RECOVERY_INVENTORY="$run_dir/inventory.ini" \
  RECOVERY_TARGET="$fresh-gw" RECOVERY_HOSTNAME="$fresh-gw" \
  RECOVERY_RUN=20261124T050335Z
```

The original gateway requires approval for resource use there. For an explicitly approved original-gateway drill, set `RECOVERY_MODE=original`, `RECOVERY_ORIGINAL_APPROVED=lab-gw`, `RECOVERY_HOSTNAME=lab-gw`, and select its inventory file and host alias explicitly. Set `RECOVERY_ASK_BECOME_PASS=yes` if needed. Run `make validate-live` after a drill on the original lab.

Each application uses the local Docker engine and one temporary container capped at 512 MiB and one CPU. The playbooks verify the archive manifests, reject archive links and unsafe paths, and check the planned bind mounts and isolation settings before starting the container. All binds come from the new scratch directory. Recovery containers have no network or published ports. Ansible removes the container by ID and cleans the scratch directory on normal completion or task failure.

Prometheus checks WAL replay, readiness and four representative historical series during the 30 minutes before the backup ID. Set `RECOVERY_WINDOW_SECONDS` to examine a longer window for a sparsely active lab. Grafana checks database health and retrieves the restored dashboard UID and panels via its versioned API. An empty HomeLab provider has deletion disabled, so Grafana preserves the archived dashboard without importing a new definition. By default, the container permits an anonymous Viewer only inside its isolated network namespace. To test the restored account, provide both `HOMELAB_RECOVERY_GRAFANA_USER` and `HOMELAB_RECOVERY_GRAFANA_PASSWORD` in the controller environment through a private prompt or secret manager, and unset them after execution. Account authentication then substitutes for anonymous access, and the test checks the API identity as well as dashboard access. Credentials travel via standard input with Ansible logging suppressed for the check.

If the controller is killed or disconnected, inspect the selected host for containers with the `dev.homelab.recovery` label and their matching scratch binds under `/var/tmp`. Verify the container ID and scratch path before any manual cleanup. The [monitoring recovery report](tests/TEST-003-monitoring-application-recovery.md) records the prior exercise. The [completion evidence](tests/TEST-004-engineering-completion.md) records the latest validation.
