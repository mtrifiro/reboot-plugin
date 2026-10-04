---
id: client-portal-09
project: client-portal
source: "client-portal/reboot-findings.md §9"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - run/SKILL.md
  - dashboard/SKILL.md
  - inspect/SKILL.md
tags: [operations, index-gap]
cluster: "F"
still_applies: unknown
status: Open
resolved_by: ""
---

# Processes, ports, and what reads what (.env read only at process start)

**What happened.** Table: API plus state inspector at `http://127.0.0.1:9999` and `/__/inspect` (port from `.rbtrc` `dev run --port=9999`; 9991-9998 taken by sibling projects); developer dashboard at `http://127.0.0.1:9871/` (`rbt dashboard` reads files, not the running app: API, changelog and the `.feature` files); frontend at `http://localhost:5173` (Vite). `rbt dev run` reads `--env-file=.env` at process start; a hot reload does not pick up a changed `.env`, so any credential or flag change is a restart. That cost ten confusing minutes with `PORTAL_PUBLISH_EVERYTHING`. Useful inspection commands: `rbt inspect state list --type=portal.v1.Portal --application-url=http://localhost:9999`, `rbt inspect state get --type=... --id=...`, and an `OrderedMap` is two hops (the map holds a root id, the `Node` holds keys/values).

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md` (env file handling) and `inspect/SKILL.md`.

**Checked at 1.6.0.** `run/SKILL.md` (lines ~75-92) covers `.env` loading but a grep did not find the statement that a hot reload ignores `.env` changes; `inspect/SKILL.md` already shows `--application-url` usage.
