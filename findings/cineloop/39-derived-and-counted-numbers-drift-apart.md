---
id: cineloop-39
project: cineloop
source: "cineloop/reboot-findings.md §29 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: primer
names: []
tags: [pattern]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Derived and counted numbers drift apart, twice

**What happened.** Revenue is derived from seat state; order count is counted into a ledger. They disagree whenever one changes without the other. Incident 1 (ledger added after orders existed, item 36): $668 revenue, 0 orders. Incident 2 (chain reset refunded every order): $0 revenue, 15 orders. Both read as broken on the dashboard and both were 'working as coded'. Rule: every counted aggregate needs to handle both directions; a counter that only goes up disagrees with a derived figure the first time something is removed, refunded, cancelled or reversed. Add the reversal (`refund_count`) and show it ('15 refunded of 15' is honest; a bare '15' next to $0 is not). Sharper question for any dashboard tile: what happens to this number when the underlying thing is undone?

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** General design lesson rather than a Reboot-specific one; belongs in the primer.
