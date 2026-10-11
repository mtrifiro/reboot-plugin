---
id: showtime-09
project: showtime
source: "2026.08.18 reboot-findings.md #9"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [pattern, auth]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# `request is None` is a clean per-method authorization discriminator

**What happened.** When all readers declare `request=None`, one shared predicate can allow reads to any verified caller and reserve every request-carrying mutator for `context.app_internal`. Avoids a custom `Authorizer` subclass.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
