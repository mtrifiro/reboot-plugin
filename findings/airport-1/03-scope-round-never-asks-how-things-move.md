---
id: airport-1-03
project: airport-1
source: "airport-1/FINDINGS.md § Plugin skills, item 2"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - build/SKILL.md
  - web-app/references/ui-design.md
  - python/references/testing-web-app.md
tags: [negative-space, frontend, pattern]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "build/SKILL.md § Design Phase"
mechanism: prose
---
# The scope round never asks how people move things, so drag and drop is never offered

**What happened.** The brief was "manage an airport's gate assignments". The build chose a gate-by-time board as the primary view, and the main action is moving a flight to another gate. The prototype shipped click, pick a gate from a select, press Assign. The developer asked why drag and drop was not there from the start. It appeared only as a "next feature" suggestion at handoff.

**Expected.** When the view and the action together make direct manipulation the obvious interaction, the scope round asks one question about it, with a recommendation. The rule that forbids silent deviations from the brief (build Design Phase item 2) is right, but nothing turns "this is a deviation" into "so ask it in the scope round".

Suggested rule, for build Design Phase item 0: ask how items move when all three hold: (1) the primary view is positional (a timeline or Gantt, a calendar, a board with columns, a floor plan or seat map, a ranked or ordered list); (2) the main action changes position (assign to a lane or resource, reschedule, change a status column, reorder, reseat); (3) the action is frequent (many times a session by the same person). The question, one of the scope round's four, in the user's nouns: "How do controllers move a flight: drag it on the board, or pick a gate in a panel?" Options: drag on the board, with the panel kept for the keyboard (Recommended when all three hold); the panel only. Don't ask, and use the panel, when the app is phone-first, the move needs fields beyond the position (a reason, an approval), moves are rare, or a wrong move is costly and wants a confirm step anyway.

Once drag is chosen, the build must know: map each drop to one existing method (drop on a lane is `assign`, on a column `set_status`), so drag is a page change only and stays in Prove; a drop that changes two things at once (another gate and other times, from dragging diagonally) needs one method that does both, or two calls can half-apply, so name it in the scope question ("sideways drag also retimes?") and default it off; show the rule while dragging (the target highlights free or taken before the drop, from data the page already has; the backend still decides, and a refused drop snaps back with the typed error's message); keep a keyboard path (the panel stays; drag alone fails accessibility, and the click path is what most scenarios drive); tests: HTML5 drag events often defeat Playwright's `drag_to()`, so build drag on pointer events and write a custom step with `mouse.down()`, `move()` and `up()` (`testing-web-app.md`); viewers get a scenario proving nothing moves.

**Repro.** Not recorded.

**Where in the skills.** `build/SKILL.md` Design Phase item 0 (the scope questions list domain, roles, never-wrong, never interaction) and item 2 ("Implement the brief literally"); `web-app/references/ui-design.md` 02, whose table names `board` and "Places, dates" views but says nothing about how items move on them; `python/references/testing-web-app.md`, which already knows drag needs custom steps (§ The steps: `mouse.down()` / `move()` / `up()`).
