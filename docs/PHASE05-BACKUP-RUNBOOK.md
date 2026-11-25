# Storage backup and restore

The Mac archives `/srv/homelab/data/files` from `lab-storage` over the configured SSH jump. Set `HOMELAB_VOLUME` to a mounted external SSD with a `HomeLab` directory. Confirm BatchMode SSH works and pause source writes if consistency matters.

```bash
export HOMELAB_VOLUME="/Volumes/Your SSD"
ssh -o BatchMode=yes homelab-storage true
bash scripts/backup-storage.sh
bash scripts/restore-test.sh "<backup-directory-printed-by-the-backup>"
```

The backup script requires the SSD mount, streams a compressed archive, records file names and SHA-256, and publishes the completed staging directory under `HomeLab/Backups/lab-storage`. The restore script verifies and extracts the archive into a temporary directory on the same SSD, then removes that extraction. Compare the recovered sample hash against a known source hash when testing specific files. Use trusted archives only.

A separate sample restoration on the storage server produced a matching SHA-256. See the [evidence index](../evidence/README.md). The script covers file-level recovery. VM images, monitoring volumes, system configuration and secrets require separate protection. The reference SSD holds both VM files and backup copies, so an SSD loss would affect both.

See the [LaunchAgent setup](PHASE05-SCHEDULING.md) for recurring backups and the [operations runbook](RUNBOOK.md#back-up-and-test-monitoring-recovery) for monitoring backups.

## Copy a verified run to independent media

Choose a different physical disk with encryption and enough free space. Confirm the backing devices with `diskutil info` on macOS or `lsblk` on Linux. Separate volumes can share one physical disk. The copy tool checks the mounted filesystem and requires explicit physical-device confirmation.

```bash
destination=/path/on/independent/disk/private-homelab
mkdir -m 700 "$destination"
python3 scripts/copy-backup.py storage /path/to/completed/20261125T010002Z "$destination" \
  --destination-mount /path/to/mounted/filesystem --confirm-independent

bash scripts/restore-test.sh "$destination/storage-20261125T010002Z"
```

Pass `monitoring` for a completed run containing both monitoring archives and `SHA256SUMS`. Stage that run on a mounted source filesystem before the independent copy. To revalidate a copied monitoring run, place its archive pair and manifest in a restricted directory named for the original UTC run ID on the authorized test host and follow the [monitoring recovery runbook](RUNBOOK.md#back-up-and-test-monitoring-recovery).

The copy workflow verifies source and staged SHA-256, publishes the destination only after verification, and refuses existing destinations for the same run. It copies just the archives and checksum manifest, including any data contained in the archives. The scheduled storage backup still writes its normal source copy. Keep both copies outside Git. A copy to the Mac's internal disk protects against loss of the external SSD. Geographically separate storage is a separate failure boundary.

## Optional recurring off-device copy

Point the same tool at the parent of the completed source runs and identify both mounted filesystems. This invocation can run repeatedly and uses the existing copy format.

```bash
source_mount='/Volumes/Source SSD'
destination_mount='/Volumes/Independent SSD'
source="$source_mount/HomeLab/Backups/lab-storage"
destination="$destination_mount/private-homelab"
python3 scripts/copy-backup.py storage "$source" "$destination" \
  --all-completed --source-mount "$source_mount" \
  --destination-mount "$destination_mount" --confirm-independent \
  --reserve-mib 256 --keep 14
```

The job verifies both mounted filesystems and processes completed runs newest first. Each source and existing copy is checked against its SHA-256 manifest. New copies use private staging on the destination and are published after verification. A completed source with a checksum or destination conflict produces a nonzero exit. Timestamped directories without a manifest are deferred. If no completed source run can be verified, the job fails so a scheduler can surface a missing backup.

`--reserve-mib` sets the minimum free space to leave on the destination. Insufficient space or a write error leaves the source and the committed copies in place. The job emits UTC logs and a copied, already verified, deferred and failed summary. Exit 75 signals another copy process holds the destination lock. Keep logs in a private directory.

`--keep` only previews older checksum-verified copies beyond the requested count. Verification failures suppress that preview. Replication never deletes a source or committed backup. The [optional LaunchAgent example](examples/dev.homelab.off-device-copy.plist) shows schedule and log configuration for a separate job. Review the paths, device identities and time before requesting approval to enable it. Recurring off-device replication is currently unconfigured.
