---
id: crm-kit-73
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §11 Where this kit deliberately overrides a plugin skill"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - feature/SKILL.md
tags: [pattern, testing]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# The feature skill agrees each feature one at a time and asks before removing @wip; at about 50 files that is 50 round trips

**What happened.** Not a plugin error, the kit makes a different call. `feature/SKILL.md` Step 5 asks the user before removing `@wip`, and the skill agrees on each feature in plain English, one at a time. At about 50 files that is 50 round trips. The kit shows the feature list with the brief and confirms it in one breath (`intake.md` §5), grouped by milestone; that agreement covers every file on it, and `@wip` comes off when a milestone's gate passes, without asking again, unless a scenario had to change or was blocked as a kit gap.

**Expected.** Not recorded beyond the kit's own process.

**Repro.** Not recorded.

**Where in the skills.** `feature/SKILL.md` Step 5 and its per-feature agreement step.

**Checked at 1.6.0.** `feature/SKILL.md` still has "Step 5 — Ask before taking `@wip` off" and agrees on features one at a time; no batch-agreement path.
