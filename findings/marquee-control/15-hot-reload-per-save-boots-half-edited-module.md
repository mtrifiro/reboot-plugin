---
id: marquee-control-15
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 14"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/lifecycle-dev-loop.md
  - python/references/scheduling-basic.md
tags: [operations, error-text, negative-space]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# Hot-reload lands per save, so a multi-edit change can boot a half-edited module

**What happened.** An edit referencing a constant added in a second edit put the live tick chain into `NameError → TickAborted('Unknown') → retry after backoff` until the second save landed. Two facts: (a) undeclared errors in scheduled transactions do retry with backoff (typed aborts don't), so the chain self-healed; (b) make live-code edits one atomic Write per file, definitions before uses.

**Expected.** Not recorded.

**Repro.** With `rbt dev run` watching, save a servicer edit that uses a constant before saving the edit that defines it.

**Where in the skills.** `lifecycle-dev-loop.md` (Never), `scheduling-basic.md` (Limits).

**Checked at 1.6.0.** `lifecycle-dev-loop.md` § Never says to write an API (state-shape) edit once in final form while the watcher is live, but says nothing about servicer code reloading per save. `scheduling-basic.md` § Limits says a scheduled method raising `<Method>Aborted` is not retried; that undeclared errors are retried with backoff is not stated.
