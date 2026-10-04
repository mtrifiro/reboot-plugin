---
id: mattprd-11
project: mattprd
source: "2026.08.22 REBOOT_FINDINGS.md §Smaller notes"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [frontend]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Smaller notes: pinned toolchain and reactive hooks delivered

**What happened.** The plugin's pinned toolchain (`uv`, `node`, `rbt`, bundled `envoy`) made setup zero-config: `uv sync` + `rbt generate` + tests worked first try. The generated React client's reactive hooks ('live updates are free') delivered; the chat UI needed zero transport code.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked).
