---
id: restaurant-app-2-03
project: restaurant-app-2
source: "restaurant-app-2/FINDINGS.md § Plugin skills, item 2"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - build/SKILL.md
  - build/references/flywheel.md
  - web-app/references/ui-design.md
tags: [negative-space, frontend]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "build/SKILL.md § Accept the Design"
---
# The visual brief was skipped, and acceptance never shows the look

**What happened.** The design the user accepted said, in full, about the look: "Light/dark toggle, chosen accent (no brand supplied)", though the skill asked for a brief (who and on what screen, the hero view, the palette and its source, the type). The accent (mulberry `#8b3a6b`) was picked fifty minutes later inside a CSS edit, with the comment "chosen, no brand supplied", and never shown. The first the user saw of the look was the running app, and within ten minutes they rejected the colors four times ("I also hate the color choices", "New color choices are horrible", "I need better colors", "the colors still look horrible; it doesn't look cool"). Found in a 2026-10-10 review of the 2026-10-06 build transcripts; the build ran on plugin commit 8724ae3.

**Expected.** The look is part of what the user accepts. The design card and the Accept the Design review carry the five-line brief next to the rule table, and, when no brand was supplied, the one-line offer ("Reboot default; name a brand or a site to model and I'll read it"), so the user's taste is sampled at the one moment they already stop. Better: render it before code, the plugin's class page (`tools/style-check.html`) in the brief's tokens, screenshotted, so the look is seen on the template anatomy before a page exists. A grader on the acceptance card for the brief (regex: it sits late in a long message). Since the build (plugin c905da6 and later): the Design Phase asks for the five-line brief and `design-ready-for-both` grades it; the acceptance card, the review table and the stage card still carry no look line, and nothing is rendered before code.

**Repro.** Ask for an app naming no brand; at acceptance, grep the card for an accent and its source.

**Where in the skills.** `build/SKILL.md` (Design Phase, Accept the Design), `build/references/flywheel.md` (Stage cards), `web-app/references/ui-design.md` 01.

**Resolution (2026-10-10).** The Accept the Design card carries the five-line visual brief beside the rule table and, with no brand supplied, the offer of the Reboot default or a brand or site to read. Rendering the brief before code and a grader on the card remain open (wave 5).
