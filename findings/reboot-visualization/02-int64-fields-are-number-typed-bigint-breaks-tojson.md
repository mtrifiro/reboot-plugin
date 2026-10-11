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
status: Resolved
resolved_by: "python/references/react-generated-client.md § Errors you will see"
---

# int64 request fields are number-typed in the generated client; a BigInt or string breaks toJson silently

**What happened.** `SeatHoldRequest.expires_epoch_hint_s` (int64) throws `cannot encode field … to JSON` inside `reboot_web.httpCall` when the value is a `BigInt` or a string; the UI click silently no-ops (the rejection surfaces only in the console). The generated pb type is plain `number`, so pass a number. Cost: three debugging rounds, because a direct `curl` with a JSON string worked.

**Expected.** Not recorded.

**Repro.** Call a mutator whose request has an int64 field with a `BigInt` or string value.

**Where in the skills.** `python/references/react-generated-client.md` (no type-mapping note for 64-bit integers).

**Checked at 1.6.0.** Grep for `int64`/`bigint` in `python/references/react-generated-client.md` and `web-app/` found nothing. The source used the 1.4.0 protobuf-es client; whether the 1.6.0 zod-based client has the same mapping was not checked.

**Resolution (2026-10-10).** Rows in `react-generated-client.md` § Errors you will see: the UUID idempotency key; the second reader's hook throwing (1.4.0); int64 as `number`; a subscription on an unconstructed actor tearing the channel; the six-connection ceiling. The `#`-in-id trap already had its row; the `_rbt_web.ts` import failure is proto-era (1.4.0) and not carried.
