---
id: crm-kit-69
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §10"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - deploy/SKILL.md
tags: [frontend, operations]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "deploy/SKILL.md § Step 3 — Deploy the backend"
---

# After any breaking backend change, republish the frontend in the same deploy

**What happened.** The old bundle keeps calling deleted methods and looks fine until someone presses that control. Publish with `wrangler pages deploy <dist> --project-name=<p> --branch=main`; without `--branch=main`, a deploy from another branch is a preview alias. Run it from the repo root, not `web/`, and pass `--force` once to create the project.

**Expected.** Republish the frontend in the same deploy as any breaking backend change.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source.

**Checked at 1.6.0.** `deploy/SKILL.md` Step 5 uses `--branch=main` (after `pages project create --production-branch=main`); nothing says a breaking backend change requires republishing the frontend in the same deploy (grep `republish`, `old bundle`).

**Resolution (2026-10-10).** Step 3 says `scripts/deploy.sh` deploys both halves and never to ship a breaking backend change `--backend-only`; the template's script builds and publishes the frontend on every full deploy.
