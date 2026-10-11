---
id: cineloop-41
project: cineloop
source: "cineloop/reboot-findings.md §31 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/servicer-authorizer.md
tags: [pattern, auth, testing]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Gate destructive tooling on the server, then hide it (Admin type)

**What happened.** The lab panel unsells other people's tickets, so hiding the button is not access control. The tab is hidden by the same `access` probe that gates the box office, and every method behind it is refused by the backend for a non-operator, with a test asserting each (`Admin.ResetShowingAborted`, `Admin.ResetAllAborted`, `Admin.RefundOrderAborted`). Putting the tools on their own `Type` made this cheap: one `authorizer()` covers a Servicer, so `Admin` owning refunds, resets and reporting means one rule protects all of them. As methods on `Chain` (which patrons must reach) the rule would have had to tell methods apart by request type, a kind of authorizer that grows a hole when someone adds a method.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E).
