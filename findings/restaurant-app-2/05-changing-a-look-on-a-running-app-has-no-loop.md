---
id: restaurant-app-2-05
project: restaurant-app-2
source: "restaurant-app-2/FINDINGS.md § Plugin skills, item 4"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - web-app/references/ui-design.md
tags: [negative-space, frontend]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "web-app/references/ui-restyle.md § Do this"
---
# Changing a look on a running app has no loop; each rejection got a new guess

**What happened.** Four palettes in nine minutes (mulberry, "Resy", "friendly", "Linear"), each applied by regex-rewriting the token block and appending a layer, while the backend was stopped, expunged and re-seeded for floor-plan changes and the scenario suite ran in the background. Screenshots came back signed out or mid-load; the user asked "are you also doing the redesign?" and "status". The agent said "I'll look at what's actually rendering before touching colors again" only after the fourth rejection. Taste words ("cleaner and more interesting", "friendly", "cool") were acted on directly each time. Found in a 2026-10-10 review of the 2026-10-06 build transcripts.

**Expected.** A short loop in `ui-design.md` for a look change on a running app: one change per turn; no backend restart in that turn; screenshot after the change and open it; tell the user what changed and where to look. After a second rejection with no source, stop guessing: offer two or three rendered candidates (the class page in each token set) or ask for a site to read. Candidates stay token sets; the chosen one is folded into `:root` and the rest deleted (13). Since the build (plugin c905da6 and later): 12 covers the build-time screenshot review and 13 the mechanics of a restyle; nothing covers iterating with the user.

**Repro.** On a running app say "I hate the colors" three times with no source; count the `:root` blocks appended to `styles.css`.

**Where in the skills.** `web-app/references/ui-design.md` (12, 13); none for iteration.

**Resolution (2026-10-10).** A new conditional reference, `ui-restyle.md` (when the user asks to change a running app's look): a source before the edit, one change per turn with no restart in it, a screenshot opened and a line on where to look, and after a second rejection with no source, rendered candidates as token sets or a site to read.
