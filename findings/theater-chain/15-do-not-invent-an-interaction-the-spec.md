---
id: theater-chain-15
project: theater-chain
source: "theater-chain/reboot-findings.md §13c"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/SKILL.md
tags: [pattern]
cluster: "G"
still_applies: yes
status: Resolved
resolved_by: "build/SKILL.md § Design Phase"
---

# Do not invent an interaction the spec did not ask for

**What happened.** The brief said patrons click seats to add them to a cart (max 8) which places a 2-minute hold on each seat. The author built a select-then-confirm flow instead (click to stage, press "Hold N seats" to commit) because staging is common on ticketing sites, producing a map full of picked seats next to a cart reading "NO SEATS HELD." The first fix made it worse: keep the staging step and add a panel explaining it. The correct implementation is literal: the click is the hold. One click fires one `User.add_seats` with a single seat and its own `hold_id`; the seat turns amber, the cart row appears, that seat's two-minute clock starts; clicking your own amber seat releases it; no confirm button. Per-seat holds mean per-seat clocks, so seats expire staggered in click order (observed: 2 held, then 1, then 0 over about nine seconds). Checkout groups by `(showing_id, hold_id)`, so eight individually-held seats become eight `confirm_seats` calls in one transaction and one `Order`. `hold_seats` is a single-actor `Writer` so eight rapid clicks are eight small serialized writes; nothing in the state model pushed toward batching, and doing so cost a round of rework.

**Expected.** Per the proposal (G), the design phase should say: implement the brief literally; list any deviation and ask before building it. The source itself does not suggest a specific skill edit.

**Repro.** Not recorded.

**Where in the skills.** `web-app/SKILL.md`, Design Phase.

**Checked at 1.6.0.** Still absent. The Design Phase in `web-app/SKILL.md` (lines 339-356) has no instruction to implement the brief literally or to ask before deviating (grep for literal / deviat found nothing).
