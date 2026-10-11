---
id: restaurant-app-3-09
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Plugin skills, item 6"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - build/SKILL.md
  - feature/SKILL.md
tags: [testing, index-gap]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "build/SKILL.md § Step 2a — Run the scenarios red"
---
# Nothing makes the red run happen before servicers are written

**What happened.** The feature skill's Step 2a (run every scenario and watch it fail for the right reason before any code) is meant to sit between build Steps 2 and 3; `build/SKILL.md` says so only in item 0 of the design phase ("do it right after Step 2, before Step 3"). The numbered build steps go shell, servicer, authorizers, frontend, tests. The agent followed the numbered list and wrote all ten servicers before running one scenario, and admitted it later; nothing in the band, `scripts/model_diff.py` or the step list caught it.

**Expected.** A numbered step, "Step 2a: Run the scenarios red", with the servicers declared and raising `NotImplementedError`. Optionally, `model_diff.py` or the band flags a servicer commit when `tests/.last-run.json` holds no run for the accepted features.

**Repro.** Follow the Step-by-Step Build Flow's numbered list as written.

**Where in the skills.** `build/SKILL.md`, Step-by-Step Build Flow; `feature/SKILL.md` Step 2a.

**Resolution (2026-10-10).** `build/SKILL.md` has a numbered Step 2a between the project shell and the servicer: servicers declared raising `NotImplementedError`, the scenarios run red with `scripts/test.sh full`; `scripts/model_diff.py` reports whether a run has happened since acceptance.
