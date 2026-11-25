# Backup reliability and retention

The LaunchAgent runner uses an advisory lock to prevent overlapping scheduled runs. It records start, success, failure and lock-contention events. After a successful run, retention preview counts only timestamped snapshots with a verified checksum. Unverified and incomplete directories remain untouched.

With the SSD mounted and `HOMELAB_VOLUME` set, preview retention from the repository root:

```bash
python3 scripts/backup-retention.py --keep 14
```

The default keeps the newest 14 verified snapshots, with a minimum of two. The scheduled job only previews deletion candidates. The retention tool requires an explicit `--apply` to remove eligible archives. Review the preview and confirm an independently stored copy before pruning.

Check `~/Library/Logs/HomeLab/backup.log` and `backup-error.log` after a scheduled run. Local logs provide diagnostics. Independent backup storage and external failure notifications remain outside the demonstrated scope.
