---
id: cineloop-18
project: cineloop
source: "cineloop/reboot-findings.md Part 2 §E"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/state-nested-models.md
tags: [negative-space, pattern, auth]
cluster: "E"
still_applies: yes
status: Open
resolved_by: ""
---

# state-nested-models.md should cover the read-model/write-model split

**What happened.** The reference covers nesting state models (don't) and sub-records (do) but not the common third case: a response model that is a per-caller projection of a state model. Returning `self.state.<collection>` verbatim is the obvious move and silently leaks other users' identifiers in any multi-tenant reader.

**Expected.** Add: do not return stored sub-records verbatim from a shared reader. When a collection carries per-owner fields (`owner_id`, `held_by`, deadlines, private notes) and callers do not own every item, declare a separate view model; compute caller-relative fields (`mine: bool`, 'my deadline') in the reader against `context.auth` and blank the rest. (See item 9.)

**Repro.** Not recorded.

**Where in the skills.** `python/references/state-nested-models.md`.

**Checked at 1.6.0.** No view-model / per-caller guidance found in `python/references/state-nested-models.md`, `mcp-ui/` or `web-app/` (grep for view model / per-caller / verbatim found only unrelated hits).
