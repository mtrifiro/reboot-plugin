---
id: student-system-09
project: student-system
source: "student-system/reboot-findings.md §9"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/rpc-calls.md
tags: [negative-space]
cluster: "8.4"
still_applies: yes
status: Resolved
resolved_by: "python/references/rpc-calls.md § Do this"
---

# Nothing in the references names the base Context type

**What happened.** `servicers/common.py` has helpers (`caller`, `event`, the `get_*` probes) called from readers, writers and transactions. Typing the parameter as `ReaderContext` made `mypy` reject `TransactionContext` callers (`Argument 1 to "caller" has incompatible type "TransactionContext"; expected "ReaderContext"`). The author fell back to `Any`. `reboot.aio.contexts.Context` exists and is the common base of all four.

**Expected.** A one-line mention in `rpc-calls.md` would have avoided the `Any`.

**Repro.** Not recorded.

**Where in the skills.** `python/references/rpc-calls.md`.

**Checked at 1.6.0.** `python/references/rpc-calls.md` ("The Context Type Must Match the Method", line ~34) lists `ReaderContext`/`WriterContext`/`TransactionContext` but no reference mentions `reboot.aio.contexts.Context` (grep found no hits).
