---
id: showtime-26
project: showtime
source: "2026.08.18 reboot-findings.md #26"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [pattern, frontend, cost]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-react-state.md § Do this"
---

# Client-side last-known-state snapshot for first paint

**What happened.** Subscription round-trips (mount, auth probe, websocket connect, subscribe, first push, plus dev-mode effect validation) put a floor under first paint. Complement reactive readers with a localStorage snapshot: paint the previous session's data in frame one and let the push channel replace it. Because hooks stream authoritative state, the cache needs no invalidation protocol: write-through on every push, read-once on mount.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
