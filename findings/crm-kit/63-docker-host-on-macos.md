---
id: crm-kit-63
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §10"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-reboot-cloud.md
  - deploy/SKILL.md
tags: [operations, error-text]
cluster: "4.4"
duplicate_of: reboot-crm-09
still_applies: no
status: Resolved
resolved_by: "python/references/lifecycle-reboot-cloud.md § Limits; deploy/SKILL.md § Step 2 — Deploy the backend to Reboot Cloud"
---

# On macOS, export DOCKER_HOST before rbt cloud up

**What happened.** `up` looks only at `/var/run/docker.sock`, which stock Docker Desktop does not create. The error says to check that the daemon is running, and it is. Fix: `export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `lifecycle-reboot-cloud.md` § Limits ("The image push needs `/var/run/docker.sock`") and `deploy/SKILL.md` Step 2.
