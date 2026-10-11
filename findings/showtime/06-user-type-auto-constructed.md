---
id: showtime-06
project: showtime
source: "2026.08.18 reboot-findings.md #6"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [auth]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# The state type named User is special

**What happened.** With `Application(oauth=...)` it is auto-constructed per signed-in identity (state id == `context.auth.user_id`). No sign-up method, and no id passed to `useUser()` in the browser. (Design-phase finding.)

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
