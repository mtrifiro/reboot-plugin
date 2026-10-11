---
id: restaurant-app-2-04
project: restaurant-app-2
source: "restaurant-app-2/FINDINGS.md § Plugin skills, item 3"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - web-app/references/ui-design.md
tags: [negative-space, frontend]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "web-app/references/ui-design.md § Do this"
---
# A look the user names is guessed from memory, not read

**What happened.** "Let's model Resy" produced a "Resy-style palette" and type rules from memory, rejected three minutes later; "use linear.app's color scheme" produced a "Linear" layer from memory, rejected two minutes later. Neither site was opened. The afternoon restyle to Reboot's brand opened reboot.dev and the running dashboard, tabulated page, ink, highlight and fonts with their source, offered a depth (colors and type, or the whole visual language), and was accepted on the first try, two minutes after "try b". Found in a 2026-10-10 review of the 2026-10-06 build transcripts.

**Expected.** 01's "Read a brand from its site, don't guess" to cover a reference look the user names ("model X", "X's color scheme") the same as their own brand: open it, read computed styles, show the table with its source, then apply; never from memory. 13 (restyle) to begin the same way. Since the build (plugin c905da6 and later): 01 has the rule for the user's brand; nothing says a named reference product is a source too, or that the table is shown before the edit.

**Repro.** On a scaffolded app say "model Resy"; check whether resy.com is opened before `styles.css` changes.

**Where in the skills.** `web-app/references/ui-design.md` 01, 13.

**Resolution (2026-10-10).** `ui-design.md` 01 treats a product the user names as a source like their own brand: open it, read, show the table, then apply, never from memory; `ui-restyle.md` begins the same way.
