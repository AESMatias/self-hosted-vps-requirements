# How much RAM does Nextcloud need?

**158 MB idle, 200 MB peak while booting.** The smallest VPS that fits is **1 GB RAM**.

Measured on 2026-11-10 by running the [`compose.yml`](compose.yml) in this folder. These are measurements, not the vendor's published minimums.

| Metric | Value |
|---|--:|
| Idle RAM | 158 MB |
| Peak RAM while booting | 200 MB |
| Containers | 2 |
| Image size on disk | 2776 MB |
| Time from start to idle | about 67 s |
| Smallest VPS that fits | 1 GB RAM |

Images: `postgres:17`, `nextcloud:latest`. Test machine: Ubuntu 24.04.5 LTS, x86_64, 4 vCPU, 7.8 GB RAM, Docker 29.8.1.

Idle means freshly installed, no users and no data. Real use needs more; see [how the VPS size is chosen](../../README.md#how-the-vps-size-is-chosen).

## Run it

```bash
ADMIN_PASSWORD='pick-a-strong-one' docker compose up -d
```

Or deploy this exact file to a new VPS in one click:

[![Deploy on Hostinger](https://assets.hostinger.com/vps/deploy.svg)](https://www.hostinger.com/docker-hosting?compose_url=https://raw.githubusercontent.com/AESMatias/self-hosted-vps-requirements/main/apps/nextcloud/compose.yml)

Open the app as soon as it starts and create the admin account. Until you do, anyone who finds the port can.

## A VPS that fits

- **Vultr**: any Cloud Compute instance with 1 GB RAM or more.
- **Hostinger**: VPS KVM 1 (4 GB RAM, the smallest plan they sell).

[All measured apps](../../README.md)
