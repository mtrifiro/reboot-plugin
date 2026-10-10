---
id: restaurant-app-2-07
project: restaurant-app-2
source: "restaurant-app-2/FINDINGS.md § Plugin skills, item 6"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - build/templates/web-app/scripts/screenshots.py
  - build/templates/both/scripts/screenshots.py
tags: [scaffold, frontend]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "build/templates/README.md § `web-app/` adds"
---
# `scripts/screenshots.py` captures before live readers deliver

**What happened.** Twice the screenshots showed skeletons ("the screenshot script just captured it too early"; "Those screenshots caught the loading placeholders"). The template waits for `networkidle` plus 500 ms, but Reboot's readers stream in after `networkidle`. This project's copy gained a wait for `.skeleton` elements to reach zero (20 s timeout) that the template still lacks: `diff` the two copies at line 72. Found in a 2026-10-10 review of the 2026-10-06 build transcripts; the template still had only the 500 ms wait at import.

**Expected.** The template's script to wait for skeletons to clear, and, since 12 now warns about the 160 ms card fade, to wait about 300 ms after setting the theme.

**Repro.** Run the template's `screenshots.py` against a page with a live reader over seeded data; open the PNG.

**Where in the skills.** `build/templates/web-app/scripts/screenshots.py`, `build/templates/both/scripts/screenshots.py`.

**Resolution (2026-10-10).** The `web-app` and `both` templates' `scripts/screenshots.py` wait for `.skeleton` elements to reach zero (20 s) after `networkidle`, then 300 ms for the card fade, before capturing.
