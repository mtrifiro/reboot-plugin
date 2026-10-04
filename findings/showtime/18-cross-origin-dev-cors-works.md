---
id: showtime-18
project: showtime
source: "2026.08.18 reboot-findings.md #18"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [frontend]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Reboot 1.4.1 handles cross-origin dev CORS out of the box

**What happened.** `/__/oauth/whoami` from the Vite origin returns `access-control-allow-origin: <origin>` and `allow-credentials: true`, so a separate-port dev frontend needs no proxy.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
