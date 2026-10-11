---
id: reboot-bluesky-09
project: reboot-bluesky
source: "REBOOT_FINDINGS.md §9"
reboot_version: 1.4.1
severity: unrated
target: framework
names:
  - python/references/react-generated-client.md
tags: [frontend]
cluster: "8.4"
duplicate_of: reboot-air-141-16
still_applies: unknown
status: Resolved
resolved_by: "python/references/react-generated-client.md § Limits"
---

# Generated React 'Partial' request types are not partial

**What happened.** `react-generated-client.md` says a reader hook's `partialRequest` 'is optional and partial: every field has a default', but the emitted TypeScript types require every field (`{ cursor: string; limit: number }`), so every call site must pass `cursor: ""` explicitly.

**Expected.** Emit `Partial<...>`-shaped types to match the documented contract.

**Repro.** Not recorded.

**Where in the skills.** `react-generated-client.md` (lines 42-52 describe `Foo.PartialBarRequest`).
