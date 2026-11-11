# Self-hosted VPS requirements

**How much RAM does n8n, Nextcloud, WordPress or Ghost actually need?** This repo answers that with measurements instead of guesses: every app is started from a plain `docker compose` file, left to settle, and its memory is read from the kernel's own counters.

Use it to pick the smallest VPS that will run what you want to self-host.

## Results

<!-- results:start -->
| App | Containers | Idle RAM | Boot peak | Image size | Smallest VPS |
|---|--:|--:|--:|--:|--:|
| [Vaultwarden](apps/vaultwarden/) | 1 | 7 MB | 7 MB | 416 MB | **1 GB** |
| [Portainer CE](apps/portainer/) | 1 | 18 MB | 18 MB | 201 MB | **1 GB** |
| [PostgreSQL](apps/postgres/) | 1 | 23 MB | 24 MB | 646 MB | **1 GB** |
| [code-server (VS Code in the browser)](apps/code-server/) | 1 | 55 MB | 55 MB | 1500 MB | **1 GB** |
| [Nginx Proxy Manager](apps/nginx-proxy-manager/) | 1 | 65 MB | 103 MB | 1910 MB | **1 GB** |
| [Gitea](apps/gitea/) | 1 | 78 MB | 78 MB | 262 MB | **1 GB** |
| [Uptime Kuma](apps/uptime-kuma/) | 1 | 107 MB | 138 MB | 2530 MB | **1 GB** |
| [WordPress](apps/wordpress/) | 2 | 121 MB | 121 MB | 1578 MB | **1 GB** |
| [Umami](apps/umami/) | 2 | 157 MB | 168 MB | 2006 MB | **1 GB** |
| [Nextcloud](apps/nextcloud/) | 2 | 158 MB | 200 MB | 2776 MB | **1 GB** |
| [Jellyfin](apps/jellyfin/) | 1 | 162 MB | 163 MB | 2490 MB | **1 GB** |
| [Actual Budget](apps/actual-budget/) | 1 | 239 MB | 239 MB | 560 MB | **1 GB** |
| [Grafana + Prometheus](apps/grafana-prometheus/) | 2 | 313 MB | 314 MB | 2409 MB | **1 GB** |
| [n8n](apps/n8n/) | 1 | 422 MB | 907 MB | 1940 MB | **2 GB** |
| [Ghost](apps/ghost/) | 2 | 643 MB | 710 MB | 2240 MB | **2 GB** |
| [Open WebUI](apps/open-webui/) | 1 | 915 MB | 1073 MB | 6460 MB | **2 GB** |
| [Minecraft (Java, vanilla)](apps/minecraft/) | 1 | 994 MB | 994 MB | 1300 MB | **2 GB** |

Last measured 2026-11-11 on Ubuntu 24.04.5 LTS, x86_64, 4 vCPU, 7.8 GB RAM, Docker 29.8.1. Raw numbers: [`data/results.json`](data/results.json).

## A VPS for each size

**1 GB apps**

- **Vultr**: any [Cloud Compute](https://www.vultr.com/promo/try200/?ref=9931816) instance with 1 GB RAM or more.
- **Hostinger**: [VPS KVM 1](https://www.hostinger.com/vps-hosting?REFERRALCODE=R79AESMATPOE) (4 GB RAM, the smallest plan they sell).

_These are affiliate/referral links: they cost you nothing and help keep the measurements updated._

**2 GB apps**

- **Vultr**: any [Cloud Compute](https://www.vultr.com/promo/try200/?ref=9931816) instance with 2 GB RAM or more.
- **Hostinger**: [VPS KVM 1](https://www.hostinger.com/vps-hosting?REFERRALCODE=R79AESMATPOE) (4 GB RAM, the smallest plan they sell).

_These are affiliate/referral links: they cost you nothing and help keep the measurements updated._
<!-- results:end -->

## What the columns mean

- **Idle RAM**: memory used by all of the app's containers once it has finished starting and is doing nothing. Fresh install, no users, no data.
- **Boot peak**: the highest memory seen while the app was starting. Installers and database migrations often need more than the app does at rest.
- **Image size**: disk used by the Docker images, before any of your own data.
- **Smallest VPS**: the smallest common plan size that fits, using the rule below.

## How the VPS size is chosen

```
needed = max(idle RAM x 1.5, boot peak) + 400 MB
```

The 400 MB is for the operating system and the Docker daemon. The result is rounded up to the next common plan size: 1, 2, 4, 8, 16 or 32 GB.

This sizes one app for one person or a small team. Add headroom if you expect real traffic, large uploads, many workflows, or several apps on the same server. When several apps share a server, add their idle figures together and count the 400 MB once.

## How it is measured

[`measure.py`](measure.py) does this for each folder in [`apps/`](apps/):

1. `docker compose up -d`.
2. Reads each container's memory and CPU counters from the Docker Engine API every 5 seconds.
3. Waits at least 60 seconds, then until CPU stays under 10% of one core for eight samples in a row. That is "idle". It gives up after 5 minutes and marks the result.
4. Records the average memory of those last eight samples (idle) and the highest sample seen (boot peak).
5. Fails the app if any container restarted, because a crash-looping container looks idle while it waits.
6. `docker compose down -v`.

Memory here is what the kernel cannot give back: the cgroup's usage minus page cache, plus shared memory. `docker stats` includes part of the page cache, and that made the same app read 6 MB or 88 MB depending on what had run before it. Excluding the cache makes the numbers repeatable to within a few MB.

## Limitations

- Idle is not load. A WordPress site with traffic or an n8n instance running heavy workflows will use more.
- Memory is sampled every 5 seconds, so a very short spike during boot can be missed.
- Page cache is excluded. An app runs without it, but disk-heavy apps are faster when there is spare RAM for it.
- Numbers are for the image tags in each `compose.yml` on the date shown. Apps change between versions.
- The test machine's CPU architecture is shown under the table. Memory use on x86-64 can differ slightly.

## Reproduce it

You need Docker with the Compose plugin and Python 3.9 or newer. No Python packages are required.

```bash
python3 measure.py            # every app; takes a while because it pulls every image
python3 measure.py n8n ghost  # only these
```

Results are written to [`data/results.json`](data/results.json) and the tables are regenerated.

## Add an app

1. Create `apps/<app-name>/compose.yml`. The first line must be `# name: Display Name`.
2. Run `python3 measure.py <app-name>`.
3. Open a pull request with the compose file and the regenerated files.

Do not publish database ports, and take any admin password from `${ADMIN_PASSWORD:?set ADMIN_PASSWORD}` instead of hard-coding one.

## License

[MIT](LICENSE)
