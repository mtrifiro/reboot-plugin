---
id: theater-network-04
project: theater-network
source: "theater-network/docs/reboot-findings.md §4"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-initialize-hook.md
  - python/references/patterns-idempotency.md
tags: [error-text, seeding]
cluster: "C"
still_applies: no
status: Obsolete
resolved_by: ""
---

# Repeated calls on one actor from one context need an idempotency alias

**What happened.** Error: `ValueError: To call 'AddShowing' of 'amc-boston-common' more than once using the same context an idempotency alias or key must be specified`. Seeding loops (`initialize` adding four showings per theater) must use `ref.idempotently(alias=f"add-{showing_id}").add_showing(...)`. The alias also makes a re-run of `initialize` a memoized replay under the same context; a real second boot gets a fresh context and re-executes, which the additive seeding relies on.

**Expected.** Not recorded.

**Repro.** Loop in `initialize` calling `add_showing` on the same theater actor several times without an alias.

**Where in the skills.** `python/references/lifecycle-initialize-hook.md`.

**Checked at 1.6.0.** `python/references/lifecycle-initialize-hook.md` lines 12-17 and the section 'Calling the Same Method More Than Once' (line 78+) give the exact error text and the `.idempotently("alias")` fix. The re-run-versus-second-boot memoization point was not found.
