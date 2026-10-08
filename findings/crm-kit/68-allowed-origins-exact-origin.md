---
id: crm-kit-68
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §10"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - deploy/SKILL.md
  - web-app/references/react-client.md
tags: [auth, operations]
cluster: "4.2"
duplicate_of: cineloop-30
still_applies: no
status: Resolved
resolved_by: "deploy/SKILL.md § Step 4 — Allow the frontend's origin on the backend"
---

# List the frontend's exact origin in OAuth(allowed_origins=[...]): scheme://host[:port], no path, slash or wildcard

**What happened.** Leaving it unset in production refuses the start. A wrong entry CORS-blocks every sign-in. A custom domain means redeploying the backend, not just changing DNS.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `deploy/SKILL.md` Step 3: exact origins, no trailing slash or path; unset in production fails startup; then redeploy with `rbt cloud up`.
