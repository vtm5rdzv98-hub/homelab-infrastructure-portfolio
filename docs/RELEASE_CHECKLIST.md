# Release checklist

Use a feature branch and pull request for changes to this portfolio repository. Start release verification from a fresh checkout.

## Verify the candidate

1. Run `make validate` and check the corresponding GitHub Actions run. Record the local and CI results separately. CI checks the repository and does not access the Mac or its VMs.
2. Run the nine read-only checks with `make validate-live` when the original VMs are available. Record the result in the [verification record](tests/TEST-004-engineering-completion.md).
3. Review the archive and replication status in the [backup runbook](PHASE05-BACKUP-RUNBOOK.md) and [scheduling notes](PHASE05-SCHEDULING.md). The original storage LaunchAgent's calendar firing and a one-time independent copy have passed. The off-device job requires separate approval before enabling a schedule.
4. Review the tracked files and proposed history for credentials, private host identities, local paths, raw logs, backups, VM disks and Grafana databases. Run `git diff --check` and review the PR's changed files. Obtain the owner's approval before changing repository visibility.

## Confirm the scope of acceptance

- The fresh VirtualBox rebuild passed, including storage isolation after reboot, persistent ext4, an SFTP round trip, nine health checks and a zero-change Ansible repeat.
- Isolated Prometheus restored historical query data, and isolated Grafana returned the archived dashboard and panels through its API.
- The 20:00 storage calendar firing and a one-time copy to an independent physical disk passed checksum verification. The copied storage archive was extracted in isolation.
- Grafana authentication with the original account credentials, recovery from complete physical-device loss, and measured recovery time and recovery point objectives remain unverified. See [current project status](PROJECT_STATUS.md).

## Portfolio history

The portfolio starts at one root commit from a reviewed file export. The source repository's Git history and raw evidence remain private. Verify that only approved evidence and public commit attribution are present before release.
