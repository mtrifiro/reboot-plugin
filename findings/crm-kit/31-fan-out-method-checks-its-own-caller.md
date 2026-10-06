---
id: crm-kit-31
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §4"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/servicer-authorizer.md
tags: [auth, negative-space]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# A client- or MCP-facing method that fans out must check its own caller; its nested calls pass every app-internal gate

**What happened.** A client- or MCP-facing method that fans out across the data makes nested calls that arrive app-internal and pass every "teammate or internal" gate without the allowlist. Rule: such a method checks its own caller, decides caller-dependent things first, and passes the answers in.

**Expected.** Fan-out methods authorize their own caller before fanning out.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source.

**Checked at 1.6.0.** `servicer-authorizer.md` § Do this lists tokenless call paths and § Never says nested calls are app-internal with `context.auth` `None`; neither says that an externally facing fan-out therefore bypasses the gates on what it reads (grep `fan`, `app-internal`).
