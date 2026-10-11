---
id: theater-chain-02
project: theater-chain
source: "theater-chain/reboot-findings.md §2"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/scheduling-basic.md
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Model expiry as a token not as a timestamp comparison

**What happened.** The naive design (store `expires_at_ms`, compare to `now` in readers/writers) is unavailable (§1) and wrong anyway because a reader cannot mutate, so an expired seat would read as held until something wrote. What worked: `hold_seats` stamps each seat with a caller-supplied `hold_id` and schedules `expire_hold(hold_id, seat_ids)` at `when=+120s`; `expire_hold` releases exactly the seats still carrying that hold id (a seat purchased, released, or re-held under a newer id does not match; no clock is read); `confirm_seats` checks `status == held and hold_id == <mine>`. Consequences: the stored `expires_at_ms` is display-only (drives the cart countdown; a client lying about its clock only lies to itself while the server-measured `when=` still releases on time); every state transition is a write so reactive readers push it, and expiry animates live on 200 seats for every viewer with no polling.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** No skill is named; related to `python/references/scheduling-basic.md`.

**Checked at 1.6.0.** Not checked; this item is a record of what worked (target positive).
