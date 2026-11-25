# Build guide

Use [fresh deployment](FRESH_DEPLOYMENT.md) for the scripted Ubuntu Cloud and Ansible bootstrap. Sections 1 and 3 below describe the manual path and the reference lab layout.

## 1. Bootstrap VirtualBox and Ubuntu

Run `bash scripts/host_audit.sh` on the Mac. Install a VirtualBox build compatible with the host and create two Ubuntu Server VMs on an external SSD. The reference lab used Ubuntu Server 26.04.1 LTS. Enable the Ubuntu SSH server at install time and create a sudo-capable `labadmin` operator. Use the VirtualBox console for the initial network and SSH configuration.

| VM | Adapter 1 | Adapter 2 |
| --- | --- | --- |
| `lab-gw` | NAT, with host TCP `127.0.0.1:2222` forwarded to guest TCP 22 | Internal Network `homelab-private` |
| `lab-storage` | Temporary NAT while installing packages, disabled for the deployed isolation policy | Internal Network `homelab-private` |

Configure a static address on each internal interface with Netplan. Check interface names with `ip -br link` first. The lab used these addresses and left the internal interfaces without a default route. Use `sudo netplan try` from the console.

```yaml
network:
  version: 2
  ethernets:
    enp0s8:
      dhcp4: false
      addresses: [10.20.0.10/24]  # Use 10.20.0.20/24 on lab-storage.
```

Keep gateway NAT configured for DHCP. Provision a private SSH key on the Mac, install its **public** key on both VMs, and verify the host fingerprints through the VM consoles before trusting them. Add these entries to your local SSH config. Set a local `IdentityFile` and `IdentitiesOnly yes` under each alias if you use a dedicated key.

```sshconfig
Host homelab
    HostName 127.0.0.1
    Port 2222
    User labadmin

Host homelab-storage
    HostName 10.20.0.20
    User labadmin
    ProxyJump homelab
```

Test both aliases in separate sessions before enforcing key-only access. On a fresh VM, review the intended UFW allows from the [architecture](ARCHITECTURE.md), add the SSH allow rules before enforcing deny-by-default, and keep the console available. Storage needs only TCP 22 and 9100 from the gateway on the internal interface. For storage, provision an ext4 logical volume and persistent fstab entry for `/dev/ubuntu-vg/data-lv` at `/srv/homelab/data` using its actual filesystem UUID. Create `/srv/homelab/data/files` with the required SFTP operator permissions. Hands-on disk selection and formatting belong to initial provisioning on a fresh VM.

Use the repository [SSH drop-in](../ansible/files/00-homelab-hardening.conf) on each VM after verifying key access. Use `sudo sshd -t` and `sudo sshd -T` to check syntax and effective settings before reloading SSH with the console available.

Install Docker Engine and the Compose plugin on the gateway. On storage, install Node Exporter before disabling NAT. The lab inventory expects a systemd unit named `node-exporter`. If your installation provides a differently named unit, align the service checks and manage playbook with that name. Verify the exporter listens on TCP 9100 and access matches UFW policy. Confirm storage has no default route after turning off temporary NAT.

## 2. Prepare the Ansible controller

From the repository root on the Mac, use a compatible Python and create the controller environment if needed.

```bash
python3 -m venv ~/.venvs/homelab-ansible
source ~/.venvs/homelab-ansible/bin/activate
python -m pip install 'ansible-core==2.22.0'
ansible-galaxy collection install -r ansible/collections/requirements.yml
ansible -i ansible/inventory/hosts.ini homelab_nodes -m ansible.builtin.ping
```

Align the inventory with your aliases. Several playbooks target the documented network, service names, Docker paths and operator account. Review those values before using a different topology. Audit playbooks `01`, `03`, `05`, `06` and `08` document the expected host, SSH, firewall and storage states. A useful first step on an existing lab is comparing the audits with the recorded topology. Firewall and mount playbooks `07` and `09` adopt an already matching firewall/mount baseline. Playbook `09` requires the operator-confirmed value via `-e data_uuid=<filesystem-uuid>`.

## 3. Deploy the services on a fresh gateway

The canonical assets are [portal](../services/portal/) and [monitoring](../services/monitoring/). The copy and creation commands below are for empty deployment paths on a new gateway. On the existing lab, use the [runbook](RUNBOOK.md) and the guarded adoption checks in playbooks `11–13`.

On the Mac, from the repository root:

```bash
ssh homelab 'mkdir -p ~/homelab-services'
scp -r services/portal services/monitoring homelab:~/homelab-services/
```

On the gateway:

```bash
cd ~/homelab-services/portal
sudo docker compose config --quiet
sudo docker compose up -d

cd ~/homelab-services/monitoring
install -d -m 700 secrets
if [ ! -e secrets/grafana_admin_password ]; then
  (umask 077; openssl rand -hex 24 > secrets/grafana_admin_password)
  chmod 0444 secrets/grafana_admin_password
fi
sudo docker compose -f compose.yaml -f compose.grafana.yaml -f compose.alerts.yaml config --quiet
sudo docker compose -f compose.yaml -f compose.grafana.yaml -f compose.alerts.yaml up -d
```

On a fresh deployment, the private directory restricts access on the host while the file is readable by the Grafana process through the Compose secret mount. See [Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/). Handle the bootstrap password in a private session and change it at first login. From the Mac, run `bash scripts/verify-lab.sh` and use the tunnels in the [runbook](RUNBOOK.md).

## 4. Validate source changes without touching the VMs

```bash
make validate
```

Use `make validate-live` from the Mac to verify an existing lab. See the [verification matrix](TEST_PLAN.md) for evidence and scope.
