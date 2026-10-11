---
id: theater-network-24
project: theater-network
source: "theater-network/docs/reboot-findings.md §24"
reboot_version: 1.4.0
severity: unrated
target: framework
names:
  - python/references/react-generated-client.md
tags: [frontend, version-drift]
cluster: "8.4"
duplicate_of: reboot-air-141-16
still_applies: unknown
status: Resolved
resolved_by: "python/references/react-generated-client.md § Limits"
---

# Generated TS request types use z.infer where z.input belongs

**What happened.** Every generated request model with a defaulted field is REQUIRED at the call site: the zod schema carries `.default(0)`, but the exported type is `z.infer` (output type, defaults applied) rather than `z.input` (defaults optional). `ensureSeats({})` fails `tsc` against a field the runtime would default, and it blocked the app's first production build.

**Expected.** Defaulted fields optional at the call site (`z.input`). Workaround: pass the default explicitly (`{ startAfterSeconds: 0 }`). One-line codegen fix upstream.

**Repro.** `tsc` on a call omitting a defaulted request field.

**Where in the skills.** Codegen issue; a workaround line could go in `react-generated-client.md` Errors.

**Checked at 1.6.0.** Not checked against 1.6.0 codegen (proto-era naming in source). No mention in `python/references/react-generated-client.md`.
