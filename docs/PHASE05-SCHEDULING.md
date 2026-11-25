# Scheduled storage backups on macOS

The optional user LaunchAgent `dev.homelab.storage-backup` defaults to 20:00 local time. It runs installed copies of the repository scripts and writes logs under `~/Library/Logs/HomeLab`. The Mac user session, the two VMs and the SSD must be available. Keep the SSH key passphrase protected and verify noninteractive authentication for both aliases in the LaunchAgent's environment.

On a Mac where you intend to install or update the job, run from the repository root:

```bash
export HOMELAB_VOLUME="/Volumes/Your SSD"
bash scripts/install-backup-schedule.sh 20 0
launchctl kickstart "gui/$(id -u)/dev.homelab.storage-backup"
```

The installer passes `HOMELAB_VOLUME` to the job and installs a stable copy under `~/Library/Application Support/HomeLab/bin`. Read the latest stdout and error logs for a verified backup and a success marker. Confirm a new timestamped archive exists and run the isolated restore in the [backup runbook](PHASE05-BACKUP-RUNBOOK.md).

A successful kickstart tests an on-demand LaunchAgent run. Confirm a new log entry after the next scheduled interval to establish calendar execution. The retained logs include both successful runs and skipped or failed entries. The [retention notes](PHASE05-RELIABILITY.md) cover overlap protection and retention previews.

### Interpreting a last exit code of 75

In `scripts/backup-orchestrator.py`, exit `75` is deliberately used for **lock contention**: a second invocation detected that a backup process was already running, so it skipped. Do not conclude that the backup failed solely from this value. Check `backup.log` and `backup-error.log` for a subsequent `SUCCESS`, an actual `FAILED`, or a lingering process. If the job regularly reports `SKIPPED`, investigate overlapping kickstarts or backup duration before changing the schedule. Successful on-demand execution is not evidence that `StartCalendarInterval` fired; confirm a successful run at the next scheduled time. See [release checklist](RELEASE_CHECKLIST.md).

## Calendar execution observed

On November 24, 2026, macOS unified logs recorded `StartCalendarInterval` just before 20:00 EST. The matching storage backup started at 20:00:00, passed SHA-256 validation and logged success at 20:00:03. The job's last exit code was 0. The earlier lock-contention record preceded the successful run. See the [completion evidence](tests/TEST-004-engineering-completion.md).

The 20:00 job produces the source backup. The optional [off-device replication job](PHASE05-BACKUP-RUNBOOK.md#optional-recurring-off-device-copy) has a separate configuration and remains unconfigured.
