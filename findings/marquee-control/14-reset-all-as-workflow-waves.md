---
id: marquee-control-14
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 13 (second paragraph)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/servicer-transaction.md
  - python/references/servicer-workflow-calls.md
tags: [pattern, cost]
cluster: ""
duplicate_of: cineloop-40
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Never; python/references/servicer-workflow-calls.md § Scales as"
---

# Reset All as a workflow: one directory read, then gathered writer waves of 16 (48 showings in about 2 s)

**What happened.** `Chain.reset_all` (Writer) does nothing but `self.ref().schedule().run_reset(context)`; the `run_reset` Workflow reads the directory once (`Chain.ref().read(context)`, default per-workflow scope) and fires bare `Showing.reset` writer calls in `asyncio.gather` waves of 16, each scoped `.per_workflow(f"Reset {id}")` so replays skip completed resets. 48 showings clear in about 2 s wall-clock, versus the 10-20 s a 48-participant transaction would serialize into.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `servicer-transaction.md`, `servicer-workflow-calls.md`. Same lesson as cineloop-40.

**Checked at 1.6.0.** `servicer-transaction.md` § Never says to iterate N things in a Workflow with `.per_workflow(f"... {id}")` per step; `servicer-workflow-calls.md` § Never allows gathering writer calls (not transactions) and § Scales as gives about 20 concurrent as the sweet spot.
