---
id: reboot-visualization-02
project: reboot-visualization
source: "v 1.4.1 Reboot/reboot-visualization/docs/reboot-learnings 03.md §2"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [frontend, error-text, negative-space]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---

# int64 request fields are number-typed in the generated client; a BigInt or string breaks toJson silently

**What happened.** `SeatHoldRequest.expires_epoch_hint_s` (int64) throws `cannot encode field … to JSON` inside `reboot_web.httpCall` when the value is a `BigInt` or a string; the UI click silently no-ops (the rejection surfaces only in the console). The generated pb type is plain `number`, so pass a number. Cost: three debugging rounds, because a direct `curl` with a JSON string worked.

**Expected.** Not recorded.

**Repro.** Call a mutator whose request has an int64 field with a `BigInt` or string value.

**Where in the skills.** `python/references/react-generated-client.md` (no type-mapping note for 64-bit integers).

**Checked at 1.6.0.** Grep for `int64`/`bigint` in `python/references/react-generated-client.md` and `web-app/` found nothing. The source used the 1.4.0 protobuf-es client; whether the 1.6.0 zod-based client has the same mapping was not checked.
