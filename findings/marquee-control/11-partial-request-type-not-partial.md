---
id: marquee-control-11
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 11"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [frontend, version-drift]
cluster: ""
duplicate_of: reboot-air-141-16
still_applies: no
status: Resolved
resolved_by: "python/references/react-generated-client.md § Limits"
---

# The Partial<Method>Request TS type is not partial in the 1.4.1 codegen

**What happened.** `export type PartialAddSeatRequest = AddSeatRequest` in the 1.4.1 codegen, so adding a field to a request Model breaks every existing frontend call site until it passes the field (zero value is fine).

**Expected.** Not recorded.

**Repro.** Add a field to a request model; rebuild the frontend.

**Where in the skills.** `python/references/react-generated-client.md`. Same gap as reboot-air-141-16.

**Checked at 1.6.0.** `react-generated-client.md` § Limits now says that before 1.6.0 (observed 1.4.1, 1.5.0) every field was required, and at 1.6.0 `Partial<Method>Request` is `z.input` so fields with a default may be omitted.
