---
id: crm-kit-67
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §10"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-reboot-cloud.md
  - deploy/SKILL.md
  - inspect/SKILL.md
tags: [operations, auth]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# Use the printed Cloud URL as-is on port 443; the references still say :9991

**What happened.** The printed URL is `https://<app-id>.<cell>.rbt.cloud`, on port 443; the references still say `:9991`. The OAuth callback is `<origin>/__/oauth/callback` (note the `/__/`). A Google client must be of type **Web application**, and `localhost` and `127.0.0.1` are distinct origins. §11: `lifecycle-reboot-cloud.md` and `deploy/SKILL.md` show `:9991` URLs.

**Expected.** Use the printed URL as-is.

**Repro.** Not recorded.

**Where in the skills.** `lifecycle-reboot-cloud.md`, `deploy/SKILL.md` (§11).

**Checked at 1.6.0.** Still `:9991` in `lifecycle-reboot-cloud.md` (lines ~70-72), `deploy/SKILL.md` (~80, ~121) and `inspect/SKILL.md` (~55, ~75). `/__/oauth/callback` is documented (`deploy/SKILL.md`, `web-app/SKILL.md`) and "Web application" in `mcp-ui/references/auth-oauth-providers.md`.
