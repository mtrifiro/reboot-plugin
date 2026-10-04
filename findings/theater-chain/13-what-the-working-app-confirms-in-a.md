---
id: theater-chain-13
project: theater-chain
source: "theater-chain/reboot-findings.md §13"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# What the working app confirms in a real browser

**What happened.** Verified in a real browser against the running backend, not just in tests: 12 theaters, 48 showings, 200 seats each, every seat map live. Three seats picked and held, countdown ran 1:57 to 0:01, the server sweep fired, the cart emptied and the seats turned green again with no reload and no polling anywhere; the author calls this the whole architecture working (a scheduled `Writer` mutating state and a reactive reader pushing it to the browser). Checkout converted a hold to `TICKETED - 2 tickets - $33.00 - GM-8WGVZN`, seats went red, cart cleared, order appeared in will-call. Picking nine seats produced the typed `CartFullError`, rendered as "8 seats per order, and you picked 9." and nothing was held.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** No skill is named.

**Checked at 1.6.0.** Not checked; this item is a record of what worked (target positive).
