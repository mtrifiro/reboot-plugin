---
id: crm-kit-32
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §4"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/auth-claims.md
tags: [auth, pattern]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# With a verified-email allowlist, refuse to boot when a real provider is configured but the allowlist is empty

**What happened.** An empty allowlist lets any verified token in. That is right in the harness and wrong in production. `Development(claims=...)` fabricates `<name>@example.com`.

**Expected.** Boot refuses when a real provider is configured and the allowlist is empty.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source.

**Checked at 1.6.0.** `python/references/auth-claims.md` (line ~79) documents that `Development` fabricates `alice@example.com`-style claims; no reference describes a verified-email allowlist or guarding against an empty one in production (grep `allowlist`).
