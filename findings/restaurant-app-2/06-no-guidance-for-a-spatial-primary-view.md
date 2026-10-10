---
id: restaurant-app-2-06
project: restaurant-app-2
source: "restaurant-app-2/FINDINGS.md § Plugin skills, item 5"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - web-app/references/ui-design.md
  - build/SKILL.md
tags: [negative-space, frontend, seeding]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# No guidance for a spatial primary view (a floor plan, a map)

**What happened.** The restaurant's hero view is a floor plan. The first was abstract tiles; the user asked for it "to look like the layout of the restaurant in real life", then for the side panel to go compact "to create more space for the dining room", then for overlapping chairs, a glow and a gradient on occupied seats to go. The plan needed table footprints in the seed and an overlap check in code; the floor seeds once, so each geometry change cost a stop, expunge and restart. Found in a 2026-10-10 review of the 2026-10-06 build transcripts.

**Expected.** 02's "Places, dates → Map, calendar: none; build on the tokens" row to carry rules: the plan is the hero and takes the width, lists beside it go `density-compact`; geometry comes from data (footprints in the seed, non-overlap checked in code; a demo-data item for spatial domains); status on the plan follows the one-dimension rule with a legend; solid strokes, no glow or gradient; readable from across a room. A note that a seed geometry change needs the expunge cycle.

**Repro.** Ask for any app whose main object is a room, a yard or a warehouse.

**Where in the skills.** `web-app/references/ui-design.md` 02, `build/SKILL.md` Design Phase (demo data).
