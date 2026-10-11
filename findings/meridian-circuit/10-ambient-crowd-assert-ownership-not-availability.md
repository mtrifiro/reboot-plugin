---
id: meridian-circuit-10
project: meridian-circuit
source: "v 1.4.1 Reboot/meridian-circuit/docs/2026.08.18 reboot-learnings porting supabase app.md §10"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [testing, pattern]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# Beside a live simulator, assert on ownership, not availability

**What happened.** The Verification Lab's expiry scenario failed with 'expected a freed seat, saw held' while its own trace showed the guarantee holding (`checkout refused: HoldLostError`): the seat had been freed and immediately re-taken by a simulated patron within the same second. Fix: assert on ownership (the seat must not be sold to us and must no longer carry our hold id). 'Somebody else has it now' is the pool working, not a failure; any test that runs beside a live simulator needs assertions phrased this way.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded. Related to showtime-38 (staging and a third verdict state for the same environment), which takes a different fix.

**Checked at 1.6.0.** No skill discusses tests running beside a load generator; grep for `ambient`/`ownership` in `python/references/testing-*.md` found nothing relevant.
