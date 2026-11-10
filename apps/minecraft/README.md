# How much RAM does Minecraft (Java, vanilla) need?

**994 MB idle, 994 MB peak while booting.** The smallest VPS that fits is **2 GB RAM**.

Measured on 2026-11-10 by running the [`compose.yml`](compose.yml) in this folder. These are measurements, not the vendor's published minimums.

> **Note:** JVM heap is set to 1 GB (MEMORY=1G) and no players are online. Raise MEMORY and the VPS size together.

| Metric | Value |
|---|--:|
| Idle RAM | 994 MB |
| Peak RAM while booting | 994 MB |
| Containers | 1 |
| Image size on disk | 1300 MB |
| Time from start to idle | about 67 s |
| Smallest VPS that fits | 2 GB RAM |

Images: `itzg/minecraft-server:latest`. Test machine: Ubuntu 24.04.5 LTS, x86_64, 4 vCPU, 7.8 GB RAM, Docker 29.8.1.

Idle means freshly installed, no users and no data. Real use needs more; see [how the VPS size is chosen](../../README.md#how-the-vps-size-is-chosen).

## Run it

```bash
docker compose up -d
```

Or deploy this exact file to a new VPS in one click:

[![Deploy on Hostinger](https://assets.hostinger.com/vps/deploy.svg)](https://www.hostinger.com/docker-hosting?compose_url=https://raw.githubusercontent.com/AESMatias/self-hosted-vps-requirements/main/apps/minecraft/compose.yml)

Open the app as soon as it starts and create the admin account. Until you do, anyone who finds the port can.

## A VPS that fits

- **Vultr**: any Cloud Compute instance with 2 GB RAM or more.
- **Hostinger**: VPS KVM 1 (4 GB RAM, the smallest plan they sell).

[All measured apps](../../README.md)
