---
id: cineloop-27
project: cineloop
source: "cineloop/reboot-findings.md §18 (Part 3)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/testing-features.md
tags: [testing]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Tests found a real bug in my test, not my code (assert against API output, not remembered constants)

**What happened.** `test_patron_adds_seats_to_cart` initially asserted a flat seat price and failed: rows A and B are the discounted 'value' tier. The servicer was right. Failure mode: writing assertions against remembered constants instead of what the API returns. Fix: total the cart from the seat map's own prices, which is also what the UI does.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Minor positive observation.
