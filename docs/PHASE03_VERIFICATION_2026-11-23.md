# Phase 03 — Portal Deployment Verification

**Verification date:** November 23, 2026 (gateway terminal UTC clock)

## Architecture actually implemented

- Host: Intel MacBook Pro, macOS with Oracle VirtualBox; VMs stored on a 1 TB external APFS SSD.
- Gateway: `lab-gw`, Ubuntu Server 26.04.1 LTS; NAT adapter, plus `10.20.0.10/24` on named VirtualBox internal network `homelab-private`.
- Private storage: `lab-storage`, Ubuntu Server 26.04.1 LTS, `10.20.0.20/24`, NAT adapter disabled during isolation test; SSH via `ProxyJump` through gateway.
- Portal service: `nginx:stable-alpine`, deployed using Docker Compose from `services/portal/` to `~/homelab-services/portal` on the gateway.
- Host binding: `127.0.0.1:8080:80`; Mac browser access via `ssh -N -L 8080:127.0.0.1:8080 homelab`.

## Measured verification outcomes

| Test | Observed result |
|---|---|
| `docker compose ps` | `homelab-portal-portal-1` running **healthy** |
| `curl -I http://127.0.0.1:8080` | HTTP `200 OK` |
| Manual `docker compose restart portal` | Container subsequently **healthy** |
| HTTP request after restart | HTTP `200 OK` |
| `ss -lntp` | Listener bound to `127.0.0.1:8080` (`docker-proxy`) |
| Browser test | Homepage visible in Mac browser over SSH tunnel |

See the [private capture index](../evidence/README.md). The operator recorded browser access over the SSH tunnel. VM reboot recovery remains unverified.

See the [build guide](BUILD_GUIDE.md) for the current deployment and [portal recovery report](incidents/INC-002-portal-recovery.md) for the later Ansible exercise.
