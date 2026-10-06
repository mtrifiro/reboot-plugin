---
id: marquee-control-12
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 12"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/patterns-react-state.md
tags: [frontend, pattern]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "python/references/patterns-react-state.md § A deadline on every mutation in a dev-loop UI"
---

# Idempotency keys dedupe concurrent duplicates end-to-end

**What happened.** Two simultaneous `checkout` calls with the same `idempotencyKey` from the browser client both resolve success and produce one ticket, one sold seat (backend twin: two `cart.idempotently("alias").checkout` calls produce one ticket). This is the 'double submit' guarantee the lab demonstrates.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `patterns-react-state.md`.

**Checked at 1.6.0.** `patterns-react-state.md` § A deadline on every mutation in a dev-loop UI mints an `idempotencyKey` once per user intent and reuses it on retry 'so it can't apply twice'. Concurrent (rather than sequential) duplicates are not mentioned.
