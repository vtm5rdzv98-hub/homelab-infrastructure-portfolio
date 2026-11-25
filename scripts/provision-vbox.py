#!/usr/bin/env python3
"""Prepare two new VirtualBox VMs with Ubuntu Cloud and per-run SSH trust."""

import argparse
from hashlib import file_digest
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import uuid


def run(*argv, capture=False):
    result = subprocess.run(argv, check=True, text=True, capture_output=capture)
    return result.stdout if capture else None


def vbox(*argv, capture=False):
    return run("VBoxManage", *map(str, argv), capture=capture)


def names(prefix):
    if not re.fullmatch(r"homelab-fresh-[a-z0-9][a-z0-9-]{0,26}", prefix):
        raise ValueError("Use a name beginning with homelab-fresh- followed by a unique run name")
    return prefix + "-gw", prefix + "-storage"


def mac():
    return "080027" + secrets.token_hex(3).upper()


def seed(run_dir, vm, public_key, nat_mac, lan_mac, address):
    config = {
        "hostname": vm,
        "manage_etc_hosts": True,
        "disable_root": True,
        "ssh_pwauth": False,
        "users": [{
            "name": "labadmin",
            "groups": ["sudo"],
            "shell": "/bin/bash",
            "lock_passwd": True,
            "sudo": ["ALL=(ALL) NOPASSWD:ALL"],
            "ssh_authorized_keys": [public_key],
        }],
        "runcmd": [["/bin/sh", "-c",
                    "printf 'HOMELAB_HOST_KEY ' > /dev/ttyS0; "
                    "awk '{print $1, $2}' /etc/ssh/ssh_host_ed25519_key.pub > /dev/ttyS0"]],
    }

    def interface(mac_address, name, **options):
        raw = mac_address.lower()
        return {
            "match": {"macaddress": ":".join(raw[i:i+2] for i in range(0, 12, 2))},
            "set-name": name,
            **options,
        }

    path = run_dir / vm / "seed"
    path.mkdir()
    (path / "meta-data").write_text(json.dumps({"instance-id": str(uuid.uuid4()), "local-hostname": vm}))
    (path / "user-data").write_text("#cloud-config\n" + json.dumps(config) + "\n")
    (path / "network-config").write_text(json.dumps({
        "version": 2,
        "ethernets": {
            "labwan": interface(nat_mac, "labwan", dhcp4=True, optional=True),
            "lablan": interface(lan_mac, "lablan", addresses=[address], dhcp4=False,
                                dhcp6=False, **{"accept-ra": False, "optional": True}),
        },
    }))
    iso = run_dir / vm / "seed.iso"
    run("hdiutil", "makehybrid", "-quiet", "-iso", "-joliet", "-default-volume-name", "CIDATA",
        "-o", str(iso), str(path))
    return iso


def attach(vm, port, medium, device_type="hdd"):
    vbox("storageattach", vm, "--storagectl=SATA", f"--port={port}", "--device=0",
         f"--type={device_type}", f"--medium={medium}")


def create(args):
    gateway, storage = names(args.name)
    network = ipaddress.IPv4Network(args.subnet)
    private_ranges = map(ipaddress.IPv4Network, ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
    if not any(network.subnet_of(private) for private in private_ranges) or not 24 <= network.prefixlen <= 28 or network.overlaps(
            ipaddress.IPv4Network("10.0.2.0/24")):
        raise ValueError("Choose a private /24 to /28 subnet separate from VirtualBox NAT")
    gw_ip, storage_ip = network[10], network[11]
    run_dir = args.root.resolve(strict=True) / args.name
    key = args.identity.expanduser().resolve(strict=True)
    public_key = key.with_name(key.name + ".pub").read_text().strip()
    public_fields = public_key.split()
    if len(public_fields) < 2 or not public_fields[0].startswith(("ssh-", "ecdsa-")):
        raise ValueError("Expected an OpenSSH .pub file next to the controller identity")
    public_key = " ".join(public_fields[:2])
    image = args.image.resolve(strict=True)
    if image.suffix.lower() != ".vmdk" or not re.fullmatch(r"[0-9a-f]{64}", args.sha256):
        raise ValueError("Supply an Ubuntu Cloud VMDK and its published lowercase SHA-256")
    if run_dir.exists() or run_dir.is_symlink():
        raise ValueError(f"Run directory already exists: {run_dir}")
    if not 1024 <= args.port <= 65535:
        raise ValueError("Choose an unprivileged loopback SSH port")
    if min(args.gateway_ram, args.storage_ram) < 1024 or min(args.os_disk_mib, args.data_disk_mib) < 1024:
        raise ValueError("VM memory and disk sizes must each be at least 1024 MiB")
    print(f"Plan: {gateway} ({args.gateway_ram} MiB), {storage} ({args.storage_ram} MiB)")
    print(f"Internal network {args.name}: {gw_ip}, {storage_ip}; gateway SSH on 127.0.0.1:{args.port}")
    print(f"Run directory: {run_dir} (the two VMs are created powered off)")
    if not args.apply:
        return
    registered = vbox("list", "vms", capture=True)
    if any(f'"{vm}"' in registered for vm in (gateway, storage)):
        raise ValueError("One of the target VM names is already registered")
    if args.name in vbox("list", "intnets", capture=True).splitlines():
        raise ValueError("Internal network name already exists")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", args.port))
    with image.open("rb") as source:
        if file_digest(source, "sha256").hexdigest() != args.sha256:
            raise ValueError("Ubuntu image SHA-256 mismatch")
    run_dir.mkdir(mode=0o700)
    # VirtualBox can write a medium UUID into a VMDK while cloning it.
    source_copy = run_dir / "cloud-source.vmdk"
    shutil.copyfile(image, source_copy)
    # Retain partially created resources for inspection if a VBoxManage command fails.
    first_disk = None
    for vm, ram, address in ((gateway, args.gateway_ram, gw_ip), (storage, args.storage_ram, storage_ip)):
        vbox("createvm", f"--name={vm}", f"--basefolder={run_dir}", "--ostype=Ubuntu_64", "--register")
        nat_mac, lan_mac = mac(), mac()
        vbox("modifyvm", vm, f"--memory={ram}", f"--cpus={2 if vm == gateway else 1}",
             "--firmware=efi", "--boot1=disk", "--boot2=none", "--nic1=nat", "--nic2=intnet",
             f"--intnet2={args.name}", f"--mac-address1={nat_mac}", f"--mac-address2={lan_mac}",
             "--uart1=0x3F8", "4", "--uart-mode1=file", run_dir / vm / "console.log")
        if vm == gateway:
            vbox("modifyvm", vm, f"--nat-pf1=ssh,tcp,127.0.0.1,{args.port},,22")
        vbox("storagectl", vm, "--name=SATA", "--add=sata", "--controller=IntelAhci", "--portcount=3")
        disk = run_dir / vm / "system.vdi"
        vbox("clonemedium", "disk", first_disk or source_copy, disk, "--format=VDI")
        if first_disk is None:
            vbox("closemedium", "disk", source_copy)
            source_copy.unlink()
            vbox("modifymedium", "disk", disk, f"--resize={args.os_disk_mib}")
            first_disk = disk
        attach(vm, 0, disk)
        if vm == storage:
            data = run_dir / vm / "data.vdi"
            vbox("createmedium", "disk", f"--filename={data}", f"--size={args.data_disk_mib}", "--format=VDI")
            attach(vm, 1, data)
        attach(vm, 2, seed(run_dir, vm, public_key, nat_mac, lan_mac,
                           f"{address}/{network.prefixlen}"), "dvddrive")
    (run_dir / "connection.json").write_text(json.dumps({
        "name": args.name, "key": str(key), "port": args.port,
        "gateway_ip": str(gw_ip), "storage_ip": str(storage_ip),
    }, indent=2) + "\n")
    print(f"Created powered-off VMs. Start {gateway} and {storage}, then run the trust subcommand.")


def trust(args):
    run_dir = args.run_dir.resolve(strict=True)
    config = json.loads((run_dir / "connection.json").read_text())
    gateway, storage = names(config["name"])
    known_hosts = run_dir / "known_hosts"
    records = []
    for vm in (gateway, storage):
        output = (run_dir / vm / "console.log").read_text(errors="replace")
        keys = set(re.findall(r"(?m)^HOMELAB_HOST_KEY (ssh-ed25519 [A-Za-z0-9+/=]+)\s*$", output))
        if len(keys) != 1:
            raise ValueError(f"Expected one guest-generated SSH host key on the {vm} serial console")
        records.append(f"{vm} {keys.pop()}")
    # Preserve the original pinned keys when re-running trust.
    expected = "\n".join(records) + "\n"
    if known_hosts.exists():
        if known_hosts.read_text() != expected:
            raise ValueError("Guest console keys differ from the existing trusted keys")
    else:
        with known_hosts.open("x") as output:
            output.write(expected)

    for value in (config["key"], str(known_hosts)):
        if any(character in value for character in '\n\r"\\%'):
            raise ValueError("Unsupported character in SSH configuration path")
    ssh_config = run_dir / "ssh.conf"
    proxy_config = shlex.quote(str(ssh_config))
    ssh_config.write_text(f"""Host {gateway} {storage}
    User labadmin
    IdentityFile "{config['key']}"
    IdentitiesOnly yes
    BatchMode yes
    StrictHostKeyChecking yes
    UserKnownHostsFile "{known_hosts}"
    GlobalKnownHostsFile /dev/null

Host {gateway}
    HostName 127.0.0.1
    Port {config['port']}
    HostKeyAlias {gateway}

Host {storage}
    HostName {config['storage_ip']}
    ProxyCommand ssh -F {proxy_config} -W %h:%p {gateway}
    HostKeyAlias {storage}
""")
    inventory = run_dir / "inventory.ini"
    inventory.write_text(f"""[fresh_gateway]
{gateway}

[fresh_storage]
{storage}

[homelab_fresh:children]
fresh_gateway
fresh_storage

[homelab_fresh:vars]
ansible_user=labadmin
ansible_python_interpreter=/usr/bin/python3
fresh_gateway_ip={config['gateway_ip']}
fresh_storage_ip={config['storage_ip']}
""")
    print(f"SSH config: {shlex.quote(str(ssh_config))}")
    print(f"Inventory: {shlex.quote(str(inventory))}")


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("create", help="plan or register new powered-off VMs")
    prepare.add_argument("--name", required=True)
    prepare.add_argument("--root", required=True, type=Path)
    prepare.add_argument("--image", required=True, type=Path)
    prepare.add_argument("--sha256", required=True)
    prepare.add_argument("--identity", required=True, type=Path)
    prepare.add_argument("--subnet", default="10.21.0.0/24")
    prepare.add_argument("--port", default=3222, type=int)
    prepare.add_argument("--gateway-ram", default=2560, type=int)
    prepare.add_argument("--storage-ram", default=2048, type=int)
    prepare.add_argument("--os-disk-mib", default=16384, type=int)
    prepare.add_argument("--data-disk-mib", default=8192, type=int)
    prepare.add_argument("--apply", action="store_true")
    bind = commands.add_parser("trust", help="pin guest SSH keys from their VirtualBox serial consoles")
    bind.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "create":
            create(args)
        else:
            trust(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"VirtualBox provisioning failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
