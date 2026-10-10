---
id: restaurant-app-2-08
project: restaurant-app-2
source: "restaurant-app-2/FINDINGS.md § Plugin skills, item 7"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - build/SKILL.md
tags: [negative-space, frontend]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# The design evals never render; what disappointed was only visible rendered

**What happened.** Every design eval is a read-only planning session; the look graders check that the stated design names a list or a board. What the user rejected was the rendered default (an indigo accent on white panels, hairlines, a generic admin look: "it doesn't look cool"), and no eval or check sees a rendered page. Found in a 2026-10-10 review of the 2026-10-06 build transcripts.

**Expected.** A rendered check: `tools/style-check.py --browser` already renders the class page; add a judged rubric over those screenshots (hierarchy, contrast, not a generic admin template), and in the handoff, the screenshot review as an artifact: the images and one line per principle 03–09.

**Repro.** `tools/run-evals.sh`; note that no case opens a browser.

**Where in the skills.** `evals/README.md`, `tools/style-check.py`, `build/SKILL.md` (handoff).
