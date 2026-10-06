---
id: marquee-control-06
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 6"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [testing]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# The whole app came up green on the first rbt dev run

**What happened.** 14/14 user-story tests (including reactive push, a 2-patron race and expiry-timer restart recovery), mypy clean, tsc clean on the first `rbt dev run`. The author's building recipe (a personal note, `[[reference-building-reboot-apps]]`) is now three-for-three.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** The recipe is outside the plugin; not compared against the skills.
