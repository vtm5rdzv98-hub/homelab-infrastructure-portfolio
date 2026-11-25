# Narrated demonstration

Target duration is 105 seconds. Use the live lab where available and the [evidence gallery](EVIDENCE_GALLERY.md) for previously recorded behavior.

| Time | Screen | Narration |
| --- | --- | --- |
| 0–18 s | Architecture diagram | “I built this two-node Ubuntu lab on an eight-gigabyte Mac. VirtualBox forwards one localhost SSH port to the gateway. The storage server sits on an internal link and is reached from the Mac through the gateway.” |
| 18–38 s | Portal, terminal smoke check, storage route or mount | “The gateway serves this Nginx portal. The same read-only smoke check verifies the SSH jump, the persistent storage mount, the lack of a default route on storage, and local endpoints for the monitoring stack.” |
| 38–58 s | Prometheus targets, then Grafana overview | “Prometheus scrapes itself and two host exporters. Grafana visualizes both nodes, including filesystem capacity on my storage server. During a controlled exporter outage, the NodeDown rule fired and cleared after service recovery.” |
| 58–80 s | Firing and cleared captures, then storage recovery evidence | “These captures show the observed alert transitions. I also restored a stopped portal through Ansible and verified that its container ID stayed the same. A storage backup ran at the scheduled time, and I verified a copy on the Mac’s independent internal disk by extracting it.” |
| 80–105 s | Build and validation guides, then current status matrix | “The repository includes the VirtualBox and Ansible workflow for two fresh guests, an offline validation target, and separate monitoring recovery tests. The status page records which checks ran and where the lab still has recovery limits.” |

Before recording, close windows with passwords, SSH keys, host identifiers, filenames from backups, or unrelated personal information. For timed footage, show a captured passing result and keep the underlying run timestamp visible where appropriate.
