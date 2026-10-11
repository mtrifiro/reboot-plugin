---
id: showtime-01
project: showtime
source: "2026.08.18 reboot-findings.md #1"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: []
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# The pydantic API file is the single source of truth

**What happened.** Everything (servicer base classes, React hooks, request/response types) is generated from `api/<pkg>/v1/<name>.py`. Design the state model first; changing it later regenerates the world. (Design-phase finding, from reading the skill references before writing code.)

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
