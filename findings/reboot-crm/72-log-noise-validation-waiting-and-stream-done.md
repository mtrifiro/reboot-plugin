---
id: reboot-crm-72
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P4.3"
reboot_version: 1.6.0
severity: green
target: framework
names: []
tags: [operations, frontend]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Log noise: effect-validation 'Still waiting' warnings and browser 'Not expecting stream to ever be done'

**What happened.** (1) The "Still waiting for method X to complete after re-running to validate effects" warning fires at `warning` on a 5 s timer that grows by 5 s each time, so a long workflow stacks dozens of lines per sync (see P0.4(g) for proposed wording). (2) On every dev-server restart the browser console logs "[Reboot] Caught unknown exception: Not expecting stream to ever be done" for each open subscription before reconnecting; reconnect works but the message reads like a bug.

**Expected.** Fix proposed: rate-limit the warning to once per method and drop repeats to `info`; downgrade the browser message to debug when the reconnect succeeds. Recommendation: both, (2) more valuable; (1) largely disappears once expensive calls carry `effect_validation=DISABLED`.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
