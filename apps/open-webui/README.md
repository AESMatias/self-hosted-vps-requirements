# How much RAM does Open WebUI need?

**915 MB idle, 1073 MB peak while booting.** The smallest VPS that fits is **2 GB RAM**.

Measured on 2026-11-10 by running the [`compose.yml`](compose.yml) in this folder. These are measurements, not the vendor's published minimums.

> **Note:** Measured without any local model. Running models with Ollama on the same server needs RAM for the model on top of this.

| Metric | Value |
|---|--:|
| Idle RAM | 915 MB |
| Peak RAM while booting | 1073 MB |
| Containers | 1 |
| Image size on disk | 6460 MB |
| Time from start to idle | about 103 s |
| Smallest VPS that fits | 2 GB RAM |

Images: `ghcr.io/open-webui/open-webui:main`. Test machine: Ubuntu 24.04.5 LTS, x86_64, 4 vCPU, 7.8 GB RAM, Docker 29.8.1.

Idle means freshly installed, no users and no data. Real use needs more; see [how the VPS size is chosen](../../README.md#how-the-vps-size-is-chosen).

## Run it

```bash
docker compose up -d
```

Or deploy this exact file to a new VPS in one click:

[![Deploy on Hostinger](https://assets.hostinger.com/vps/deploy.svg)](https://www.hostinger.com/docker-hosting?compose_url=https://raw.githubusercontent.com/AESMatias/self-hosted-vps-requirements/main/apps/open-webui/compose.yml)

Open the app as soon as it starts and create the admin account. Until you do, anyone who finds the port can.

## A VPS that fits

- **Vultr**: any Cloud Compute instance with 2 GB RAM or more.
- **Hostinger**: VPS KVM 1 (4 GB RAM, the smallest plan they sell).

[All measured apps](../../README.md)
