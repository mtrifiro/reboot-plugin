---
id: client-portal-06
project: client-portal
source: "client-portal/reboot-findings.md §6"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
  - python/references/patterns-load-and-benchmarking.md
tags: [cost, operations, negative-space]
cluster: "D"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-load-and-benchmarking.md § Do this; python/references/servicer-workflow-external.md § Errors you will see"
---

# Dev-mode side-effect validation re-runs your blocks, and its log lines are rate-limited

**What happened.** The `INFO contexts:773: Re-running ... to validate effects` lines are not noise: Reboot re-executes memoized blocks to check they are side-effect-free. For the app that meant Drive downloads happening twice, and it is a large part of why a pass over 1,666 notes took about 70 minutes. The log lines are also rate-limited ("will silence this message for the next 5 minutes"), so counting them tells nothing reliable; twice the author drew a wrong conclusion from log-line counts and corrected it from state.

**Expected.** Measure progress from actor state (`rbt inspect`), never from log volume.

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-workflow.md`; no cost/benchmarking reference exists (proposal task D).

**Checked at 1.6.0.** Not checked in depth; `python/references/` has no text on log rate-limiting or on measuring progress from state (`patterns-load-and-benchmarking.md` does not exist yet).
