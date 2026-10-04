---
id: showtime-29
project: showtime
source: "2026.08.18 reboot-findings.md #29"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [testing, auth]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Impersonation auto-constructs the User actor in tests

**What happened.** `await rbt.create_external_context_as(name, user_id)` mints a real token, and minting constructs the `User` state as a side effect, so `User.ref(user_id)` resolves with no manual setup. Browser-side twin of finding 6.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
