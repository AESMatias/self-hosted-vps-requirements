#!/usr/bin/env python3
"""Measure idle RAM, boot peak and image size of the apps in apps/, then render the docs.

    python3 measure.py              measure every app, then render
    python3 measure.py n8n ghost    measure only these, then render
    python3 measure.py --render     render README files from data/results.json
"""
import http.client
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "results.json"

# Links used in the generated docs. An empty value leaves that link out.
REPO = "AESMatias/self-hosted-vps-requirements"  # "github-user/self-hosted-vps-requirements"
HOSTINGER_REFERRAL_CODE = ""
HOSTINGER_URL = ""
VULTR_URL = ""

OS_OVERHEAD_MB = 400  # Ubuntu + Docker daemon on an otherwise empty VPS
TIERS_GB = [1, 2, 4, 8, 16, 32]
HOSTINGER_PLANS = {4: "KVM 1", 8: "KVM 2", 16: "KVM 4", 32: "KVM 8"}  # GB RAM -> plan

MIN_WAIT, TIMEOUT, INTERVAL = 60, 300, 5  # seconds
WINDOW, IDLE_CPU = 8, 10.0  # settled = 8 samples in a row under 10% of one core


def disk_mb(text):  # `docker image ls` sizes are decimal: "436MB", "1.2GB"
    number, unit = re.fullmatch(r"([\d.]+)\s*([A-Za-z]+)", text.strip()).groups()
    return float(number) * {"kB": 1e-3, "MB": 1, "GB": 1000}[unit]


def tier_gb(idle_mb, peak_mb):
    need = max(idle_mb * 1.5, peak_mb) + OS_OVERHEAD_MB
    return next((t for t in TIERS_GB if t * 1024 >= need), TIERS_GB[-1])


assert disk_mb("436MB") == 436 and disk_mb("1.2GB") == 1200
assert tier_gb(100, 150) == 1 and tier_gb(450, 500) == 2 and tier_gb(900, 2000) == 4


def sh(*cmd, env=None):
    return subprocess.run(cmd, capture_output=True, text=True, check=True, env=env).stdout


class DockerSocket(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__("localhost")
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX)
        self.sock.connect(self.path)


def sample(sock, ids):
    """Non-reclaimable memory (MB) and cumulative CPU seconds of the containers.

    Read from the Engine API because it exposes the cgroup's memory.stat. `docker stats` counts
    part of the page cache, which made the same app read 6 MB or 88 MB depending on what ran before.
    """
    mem = cpu = 0
    for cid in ids:
        conn = DockerSocket(sock)
        conn.request("GET", f"/containers/{cid}/stats?stream=false&one-shot=true")
        s = json.load(conn.getresponse())
        m = s.get("memory_stats", {})
        stat = m.get("stats", {})
        mem += m.get("usage", 0) - stat.get("file", stat.get("cache", 0)) + stat.get("shmem", 0)
        cpu += s.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
    return mem / 2**20, cpu / 1e9


def measure(app, sock):
    env = {**os.environ, "ADMIN_PASSWORD": "measure-only"}
    compose = ["docker", "compose", "-p", f"vpsreq-{app.name}", "-f", str(app / "compose.yml")]
    try:
        # measure without publishing ports: nothing is exposed and nothing clashes with what the host already runs
        services = sh(*compose, "config", "--services", env=env).split()
        override = Path(tempfile.gettempdir()) / f"vpsreq-{app.name}.yml"
        override.write_text("services:\n" + "".join(f"  {s}:\n    ports: !reset []\n" for s in services))
        compose += ["-f", str(override)]
        sh(*compose, "up", "-d", "--quiet-pull", env=env)
        start, samples = time.time(), []  # (timestamp, MB, CPU seconds)
        while True:
            ids = sh(*compose, "ps", "-q", env=env).split()
            if not ids:
                raise RuntimeError("no running containers")
            samples.append((time.time(), *sample(sock, ids)))
            elapsed = time.time() - start
            window = samples[-(WINDOW + 1):]
            cpu = [100 * abs(b[2] - a[2]) / (b[0] - a[0]) for a, b in zip(window, window[1:])]
            settled = elapsed >= MIN_WAIT and len(cpu) == WINDOW and max(cpu) < IDLE_CPU
            if settled or elapsed >= TIMEOUT:
                break
            time.sleep(INTERVAL)
        states = sh("docker", "inspect", "-f", "{{.State.Status}} {{.RestartCount}}", *ids).splitlines()
        if len(ids) != len(services) or set(states) != {"running 0"}:
            # a container that restarted was quiet while it waited, so "idle" would be wrong
            raise RuntimeError(f"a service crashed or restarted (status, restarts): {states}")
        images = sh(*compose, "config", "--images", env=env).split()
        idle = [mb for _, mb, _ in window[1:]]
        return {
            "containers": len(ids),
            "idle_mb": round(sum(idle) / len(idle)),
            "boot_peak_mb": round(max(mb for _, mb, _ in samples)),
            "settle_seconds": round(elapsed),
            "settled": settled,
            "image_mb": round(sum(disk_mb(sh("docker", "image", "ls", "--format", "{{.Size}}", i)) for i in images)),
            "images": images,
            "measured": date.today().isoformat(),
        }
    except (subprocess.CalledProcessError, RuntimeError) as e:
        return {"error": (getattr(e, "stderr", "") or str(e)).strip()[-300:]}
    finally:
        subprocess.run([*compose, "down", "-v", "--remove-orphans"], capture_output=True, env=env)


def host_env():
    info = json.loads(sh("docker", "info", "--format", "{{json .}}"))
    return {
        "os": info["OperatingSystem"], "kernel": info["KernelVersion"], "arch": info["Architecture"],
        "cpus": info["NCPU"], "mem_gb": round(info["MemTotal"] / 2**30, 1), "docker": info["ServerVersion"],
    }


def header(slug, key):  # "# name: ..." / "# note: ..." comment at the top of compose.yml
    found = re.search(rf"^# {key}: (.+)$", (ROOT / "apps" / slug / "compose.yml").read_text(), re.M)
    return found[1].strip() if found else ""


def link(text, url):
    return f"[{text}]({url})" if url else text


def vps_options(gb):
    plan_gb = next(g for g in HOSTINGER_PLANS if g >= gb)
    lines = [
        f"- **Vultr**: any {link('Cloud Compute', VULTR_URL)} instance with {gb} GB RAM or more.",
        f"- **Hostinger**: {link(f'VPS {HOSTINGER_PLANS[plan_gb]}', HOSTINGER_URL)} ({plan_gb} GB RAM"
        + (", the smallest plan they sell)." if plan_gb > gb else ")."),
    ]
    if VULTR_URL or HOSTINGER_URL or HOSTINGER_REFERRAL_CODE:
        lines += ["", "_These are affiliate/referral links: they cost you nothing and help keep the measurements updated._"]
    return "\n".join(lines)


def app_page(slug, a, env_line):
    needs_password = "ADMIN_PASSWORD" in (ROOT / "apps" / slug / "compose.yml").read_text()
    run = ("ADMIN_PASSWORD='pick-a-strong-one' " if needs_password else "") + "docker compose up -d"
    deploy = ""
    if REPO:
        url = f"https://www.hostinger.com/docker-hosting?compose_url=https://raw.githubusercontent.com/{REPO}/main/apps/{slug}/compose.yml"
        if HOSTINGER_REFERRAL_CODE:
            url += f"&REFERRALCODE={HOSTINGER_REFERRAL_CODE}"
        deploy = f"\nOr deploy this exact file to a new VPS in one click:\n\n[![Deploy on Hostinger](https://assets.hostinger.com/vps/deploy.svg)]({url})\n"
    unsettled = "" if a["settled"] else " (still busy when the measurement window closed, so this may be high)"
    note = f"\n> **Note:** {a['note']}\n" if a["note"] else ""
    return f"""# How much RAM does {a['name']} need?

**{a['idle_mb']} MB idle, {a['boot_peak_mb']} MB peak while booting.** The smallest VPS that fits is **{a['min_vps_gb']} GB RAM**.

Measured on {a['measured']} by running the [`compose.yml`](compose.yml) in this folder. These are measurements, not the vendor's published minimums.
{note}
| Metric | Value |
|---|--:|
| Idle RAM | {a['idle_mb']} MB{unsettled} |
| Peak RAM while booting | {a['boot_peak_mb']} MB |
| Containers | {a['containers']} |
| Image size on disk | {a['image_mb']} MB |
| Time from start to idle | about {a['settle_seconds']} s |
| Smallest VPS that fits | {a['min_vps_gb']} GB RAM |

Images: {', '.join(f'`{i}`' for i in a['images'])}. Test machine: {env_line}.

Idle means freshly installed, no users and no data. Real use needs more; see [how the VPS size is chosen](../../README.md#how-the-vps-size-is-chosen).

## Run it

```bash
{run}
```
{deploy}
Open the app as soon as it starts and create the admin account. Until you do, anyone who finds the port can.

## A VPS that fits

{vps_options(a['min_vps_gb'])}

[All measured apps](../../README.md)
"""


def render():
    data = json.loads(DATA.read_text())
    e = data["env"]
    env_line = f"{e['os']}, {e['arch']}, {e['cpus']} vCPU, {e['mem_gb']} GB RAM, Docker {e['docker']}"
    ok = {slug: a for slug, a in data["apps"].items() if "error" not in a}
    rows = ["| App | Containers | Idle RAM | Boot peak | Image size | Smallest VPS |", "|---|--:|--:|--:|--:|--:|"]
    for slug, a in sorted(ok.items(), key=lambda kv: kv[1]["idle_mb"]):
        a.update(name=header(slug, "name"), note=header(slug, "note"), min_vps_gb=tier_gb(a["idle_mb"], a["boot_peak_mb"]))
        mark = "" if a["settled"] else " †"
        rows.append(f"| [{a['name']}](apps/{slug}/) | {a['containers']} | {a['idle_mb']} MB{mark} | {a['boot_peak_mb']} MB | {a['image_mb']} MB | **{a['min_vps_gb']} GB** |")
        (ROOT / "apps" / slug / "README.md").write_text(app_page(slug, a, env_line))
    block = "\n".join(rows) + f"\n\nLast measured {max(a['measured'] for a in ok.values())} on {env_line}. Raw numbers: [`data/results.json`](data/results.json)."
    if any(not a["settled"] for a in ok.values()):
        block += "\n\n† Still using CPU when the 5-minute window closed, so the idle figure may be high."
    block += "\n\n## A VPS for each size\n\n" + "\n\n".join(f"**{gb} GB apps**\n\n{vps_options(gb)}" for gb in sorted({a["min_vps_gb"] for a in ok.values()}))
    readme = ROOT / "README.md"
    readme.write_text(re.sub(r"(?s)(<!-- results:start -->).*(<!-- results:end -->)", lambda m: f"{m[1]}\n{block}\n{m[2]}", readme.read_text()))
    DATA.write_text(json.dumps(data, indent=2) + "\n")


def main(args):
    if args != ["--render"]:
        host = os.environ.get("DOCKER_HOST") or sh("docker", "context", "inspect", "-f", "{{.Endpoints.docker.Host}}").strip()
        if not host.startswith("unix://"):
            sys.exit(f"measure.py needs a local Docker socket, got {host}")
        DATA.parent.mkdir(exist_ok=True)
        data = json.loads(DATA.read_text()) if DATA.exists() else {"apps": {}}
        data["env"] = host_env()
        for app in sorted(p for p in (ROOT / "apps").iterdir() if (p / "compose.yml").exists() and (not args or p.name in args)):
            print(f"measuring {app.name} ...", flush=True)
            data["apps"][app.name] = measure(app, host.removeprefix("unix://"))
            print(f"  {data['apps'][app.name]}", flush=True)
            DATA.write_text(json.dumps(data, indent=2) + "\n")  # save after each app: a full run takes a while
    render()


if __name__ == "__main__":
    main(sys.argv[1:])
