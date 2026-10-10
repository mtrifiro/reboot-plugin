---
id: restaurant-app-3-10
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Plugin skills, item 7"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - build/SKILL.md
tags: [testing, operations]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# The full suite outlives the shell tool's timeout

**What happened.** `build/SKILL.md` Step 6 says to run the suite in the foreground "with a timeout that covers the whole run" and never leave it in the background. 47 backend scenarios took 7m46s (466 s, M-series laptop), and the agent's default 2-minute command timeout moved the run to the background anyway.

**Expected.** Give the agent the number to pass (Claude Code's Bash tool allows up to 600000 ms), and say to split the run by feature file once the suite passes about 40 scenarios.

**Repro.** A suite of about 47 scenarios under the default tool timeout.

**Where in the skills.** `build/SKILL.md` Step 6.
