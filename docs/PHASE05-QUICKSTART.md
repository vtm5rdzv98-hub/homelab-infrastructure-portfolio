# Storage backup quick start

From the repository root on macOS:

```bash
export HOMELAB_VOLUME="/Volumes/Your SSD"
ssh -o BatchMode=yes homelab-storage true
bash scripts/backup-storage.sh
bash scripts/restore-test.sh "<backup-directory-printed-by-the-backup>"
```

See the [storage backup runbook](PHASE05-BACKUP-RUNBOOK.md) for scope and safeguards.
