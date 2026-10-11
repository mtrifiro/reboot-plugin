---
id: restaurant-app-3-11
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Plugin skills, item 8"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - build/SKILL.md
tags: [negative-space]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "build/SKILL.md § Accept the Design"
---
# "Implement the brief literally" did not hold in a sibling build

**What happened.** restaurant-app-2, built from the same brief and skills on 2026-10-06, deviated with no recorded question to the developer: a draft stage before sending; "the first course of a fresh order fires at once" in place of "starters fire when sent, mains are held"; the kitchen's "window" renamed "ready" plus a fourth "picked up" status; managers allowed to void fired dishes. This build kept to the brief but still added rules (held dishes block settling, a party must fit its seats), which it did list for the developer. The rule itself came from theater-chain-15 and is `build/SKILL.md` Design Phase item 1.

**Expected.** The rule only works when the deviation list is part of what the developer accepts: a required "Beyond the brief" section on the Accept the Design card, one line per deviation with its reason, and `design/review.md` recording the developer's answer to each.

**Repro.** Compare restaurant-app-2's accepted design with the brief.

**Where in the skills.** `build/SKILL.md`, Design Phase item 1 ("Implement the brief literally"); Accept the Design.

**Resolution (2026-10-10).** The Accept the Design card carries a "Beyond the brief" list, one line per addition or change with its reason, recorded with the user's answer in `design/review.md`; the `design-accept-gate` eval gains a `beyond-the-brief` grader.
