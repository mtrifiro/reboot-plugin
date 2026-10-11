---
id: reboot-visualization-05
project: reboot-visualization
source: "v 1.4.1 Reboot/reboot-visualization/docs/reboot-learnings 03.md §5"
reboot_version: 1.4.0
severity: unrated
target: positive
names: []
tags: [testing, pattern]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# A blind adversarial pass with a footgun checklist works (validated experimentally)

**What happened.** Findings 1-4 were distilled into eight concrete smells with Reboot's lock semantics stated as axioms (`docs/adversarial-checklist.md`) and given to a fresh agent with no other context, pointed at the pre-fix backend (commit 17bfb5e) as a blind ground-truth test. It rediscovered both known deadlocks cold (the Showing read-then-schedule upgrade deadlock at the exact lines, and the seat pre-scan variant including 'the write's typed abort already covers this') and found three new issues: client-controlled `hold_seconds` with no maximum clamp (`HOLD_SECONDS` defined but unenforced, so a client can park seats forever on the anonymous API); no generation guard on the `note_seat` channel (an in-flight HELD note delivered after `run_reset`'s map clear leaves a phantom held seat no timer repairs; `force_free` sends no note at all); note payloads assembled at four drifting call sites (`"free"` literal vs `FREE=""`, working only via the else branch). A second pass over HEAD read clean (0 hits on read-then-lock / ask-permission / fan-out) and converged on the same open items; every reported hit was real or a flagged known trade-off. Cost about 2 minutes and 46k tokens per pass. The checklist encodes the runtime-invisible facts (reads pin shared locks; schedules join the lock set; bodies re-execute), so a per-commit adversarial pass catches the class serial tests cannot.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded. The phantom-held-seat issue is theater-network-25's generation fence.

**Checked at 1.6.0.** No skill ships a review checklist of lock smells; grep for `adversarial`/`checklist` found only a tag in `patterns-common-gotchas.md`.
