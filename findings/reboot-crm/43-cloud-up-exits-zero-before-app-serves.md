---
id: reboot-crm-43
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.7c"
reboot_version: 1.6.0
severity: green
target: cloud
names:
  - deploy/SKILL.md
tags: [operations]
cluster: "4.1"
still_applies: unknown
status: Resolved
resolved_by: "python/references/lifecycle-reboot-cloud.md § Limits; deploy/SKILL.md § Step 6 — Verify"
---

# rbt cloud up exits 0 about thirty seconds before the app serves

**What happened.** `rbt cloud up` printed its three URLs and exited 0. `GET /__/inspect` then returned 503 for roughly thirty seconds before turning 200. CORS headers were correct throughout (the proxy answers before the app), so a 503 carrying `access-control-allow-origin` means "still rolling out", not "misconfigured", which is not obvious when checking right after a deploy.

**Expected.** Either `up` waits for the first healthy revision, or its final line says the rollout is in progress and names the URL to poll (e.g. "rolling out; `/__/inspect` will answer 200 when ready").

**Repro.** Run `rbt cloud up`, then request `/__/inspect` immediately.

**Where in the skills.** `deploy/SKILL.md` (post-deploy verification).

**Checked at 1.6.0.** `deploy/SKILL.md` was not found to mention a 503 grace period (grep for `503`, `rolling`, `healthy`).
