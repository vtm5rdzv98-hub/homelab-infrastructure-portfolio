# Fresh deployment on VirtualBox

This workflow creates a new pair of x86-64 Ubuntu Server cloud guests with VirtualBox 7.2 and cloud-init NoCloud. Use a Mac with Python 3.11+, OpenSSH, VirtualBox, and the controller tools in the [build guide](BUILD_GUIDE.md). The reference memory allocation is 2,560 MiB for the gateway and 2,048 MiB for storage. Reserve host memory before starting the VMs. The dynamic disk capacity defaults to 16 GiB per system disk and 8 GiB for the data disk.

## Prepare the guests

1. Download the amd64 **VMDK** and obtain its SHA-256 from Canonical's [Ubuntu cloud release](https://cloud-images.ubuntu.com/releases/resolute/release/). Verify the signed checksum manifest according to your image provenance requirements. The provisioner checks the image against the supplied digest.
2. Create or select a dedicated local SSH identity with a matching `.pub` file. Protect the private key. Use a shell agent if the private key has a passphrase. The cloud-init account is `labadmin` with key-only access and passwordless sudo. This private key grants administrator access to the two new VMs.
3. Choose a fresh prefix, private subnet, loopback port, and existing parent directory on a disk with sufficient free space. Run the command first with its default plan behavior, then repeat it with `--apply` to register the guests and prepare their disks.

```bash
fresh=homelab-fresh-example
vm_parent=/path/to/existing/vm-parent
image=/path/to/ubuntu-26.04-server-cloudimg-amd64.vmdk
identity="$HOME/.ssh/homelab-fresh"
sha256='digest-from-canonical-SHA256SUMS'

python3 scripts/provision-vbox.py create \
  --name "$fresh" --root "$vm_parent" --image "$image" --sha256 "$sha256" \
  --identity "$identity" --subnet 10.21.0.0/24 --port 3222
```

The parent may contain other VMs. Each run uses a new child directory, two new VM names, and a new internal network. If a command fails midway, inspect the named run's VirtualBox settings and retain its logs. After confirming that the registered names and disk paths belong to the failed run, either repair that run or choose another fresh name. VirtualBox may register a working copy of the cloud image during cloning. The source image stays in its download location.

## Deploy and verify

Both guests use temporary NAT to install packages. Only the gateway has an inbound NAT rule, bound to Mac loopback. The NoCloud seed sets both private IPv4 addresses, disables SSH passwords and applies the public key. VM-generated host keys come from the VirtualBox serial logs, the local console trust boundary. Keep the per-run directory private.

```bash
VBoxManage startvm "$fresh-gw" --type headless
VBoxManage startvm "$fresh-storage" --type headless
run_dir="$vm_parent/$fresh"
python3 scripts/provision-vbox.py trust "$run_dir"

export ANSIBLE_SSH_ARGS="$(python3 -c 'import shlex, sys; print(shlex.join(["-F", sys.argv[1]]))' "$run_dir/ssh.conf")"
ansible-playbook -i "$run_dir/inventory.ini" \
  -e fresh_deploy=true ansible/playbooks/bootstrap-fresh.yml
```

Run `trust` after both guests produce their first-boot serial markers. If one is still starting, check its VirtualBox console or the per-guest `console.log`, then retry. The generated SSH config uses strict host-key checks for the gateway and the jump-host connection. Review the host key fingerprint through the local VM console if the serial logs or their containing directory are untrusted.

Ansible requires the actual guest hostname and private IP to match the dedicated inventory. It installs Ubuntu packages, enables UFW and key-only SSH, and provisions and mounts the storage disk at `/srv/homelab/data`. It creates the Grafana secret and deploys the canonical Nginx, Prometheus, Grafana, and exporter configuration at `/opt/homelab-services`. The playbook verifies a blank disk before formatting. Its default disk is the dedicated VirtualBox SATA port 1. Use `lsblk` and `ls -l /dev/disk/by-path` in the storage guest to verify the target before setting `fresh_data_device` for another controller. The initial blank-disk operation requires operator selection for any nonstandard topology.

After a successful bootstrap, shut down **only the new storage VM** cleanly and wait for VirtualBox to report `poweroff`. Remove its NAT adapter and boot it again to check persistent mounting and internal-only routing.

```bash
ssh -F "$run_dir/ssh.conf" "$fresh-storage" sudo shutdown -h now
# Wait for VBoxManage showvminfo "$fresh-storage" --machinereadable to report poweroff.
VBoxManage modifyvm "$fresh-storage" --nic1=none
VBoxManage startvm "$fresh-storage" --type headless

HOMELAB_SSH_CONFIG="$run_dir/ssh.conf" \
HOMELAB_GATEWAY_SSH="$fresh-gw" HOMELAB_STORAGE_SSH="$fresh-storage" \
HOMELAB_STORAGE_EXPORTER_UNIT=prometheus-node-exporter make validate-live
```

Allow the storage VM to finish booting and one Prometheus scrape interval. Cloud-init may report that the detached WAN adapter could not be renamed. The storage route and mount checks verify the resulting isolated state. The live suite verifies SSH through the jump, persistent ext4, exporter service, portal, three scrape jobs, Grafana database health, and absence of default routes on storage. To view the portal, Grafana, or Prometheus, use the [SSH tunnel in the runbook](RUNBOOK.md#health-checks-and-web-access) with the generated SSH config and gateway alias. Use a private console when retrieving the initial Grafana password from the gateway's root-only `/opt/homelab-services/monitoring/secrets` directory. Change it on first login.

For a manually installed Ubuntu pair, follow the [build guide](BUILD_GUIDE.md). The historical adoption playbooks target the original operational lab and assume its documented identities, deployment paths, and storage layout.
