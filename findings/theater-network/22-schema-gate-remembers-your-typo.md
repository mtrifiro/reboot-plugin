---
id: theater-network-22
project: theater-network
source: "theater-network/docs/reboot-findings.md §22"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/api-schema-evolution.md
  - run/SKILL.md
tags: [operations, negative-space, error-text]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# The schema gate remembers whatever booted, including your typo

**What happened.** `rbt dev run` watches and hot-restarts; the compatibility gate validates future boots against whatever schema was LAST persisted. A field momentarily committed as `list[int]`, corrected to `list[str]` seconds later, was persisted by an ill-timed hot-restart in between, and the corrected code could no longer boot: type changes are forbidden even for a mistake that lived under a minute (`has switched type from double to string ... waiting`). Cost an expunge.

**Expected.** Rule from the source: on a running dev server a schema edit is live the moment generated code changes; make API-file edits atomic (write the final form once), or stop the watcher while iterating on state shapes.

**Repro.** Edit a field type, regenerate, correct it seconds later while `rbt dev run` is watching.

**Where in the skills.** `api-schema-evolution.md` (scoped to deployed apps), `run/SKILL.md`.

**Checked at 1.6.0.** `python/references/api-schema-evolution.md` covers additive-only evolution for deployed apps; it does not say the dev watcher can persist a transient schema.
