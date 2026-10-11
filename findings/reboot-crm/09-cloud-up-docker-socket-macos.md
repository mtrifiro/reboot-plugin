---
id: reboot-crm-09
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.3"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - deploy/SKILL.md
  - python/references/lifecycle-reboot-cloud.md
tags: [operations, error-text]
cluster: "4.4"
still_applies: yes
status: Resolved
resolved_by: "python/references/lifecycle-reboot-cloud.md § Limits; deploy/SKILL.md § Step 3 — Deploy the backend"
---

# rbt cloud up only looks for /var/run/docker.sock, which stock Docker Desktop on macOS does not create

**What happened.** `rbt cloud up` built the image, then failed at the push step: `[pushing container... push failed: failed to connect to the docker API at unix:///var/run/docker.sock; check if the path is correct and if the daemon is running`. The daemon was running and the `docker` CLI worked. Docker Desktop for macOS puts its socket at `~/.docker/run/docker.sock` and selects it through the `desktop-linux` context; `/var/run/docker.sock` exists only if the user ticks "Allow the default Docker socket to be used" in Docker Desktop settings (needs admin, off by default). Workaround: `export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"`.

**Expected.** `rbt cloud up` should resolve the daemon the way other Docker tools do (`DOCKER_HOST`, then the active `docker context`, then `~/.docker/run/docker.sock`, then `/var/run/docker.sock`), and the error should name the fix. Source fix list also includes (6): `deploy/SKILL.md` prerequisites carry the macOS `DOCKER_HOST` line ("ships today").

**Repro.** Stock Docker Desktop on macOS with the default-socket option off; `rbt cloud up` any application. Blocks the first deploy.

**Where in the skills.** `deploy/SKILL.md` prerequisites; `python/references/lifecycle-reboot-cloud.md`. Target is Reboot Cloud tooling (`rbt cloud`).

**Checked at 1.6.0.** No `DOCKER_HOST`, `docker.sock` or `docker context` text in `deploy/SKILL.md` or `lifecycle-reboot-cloud.md` (grep).
