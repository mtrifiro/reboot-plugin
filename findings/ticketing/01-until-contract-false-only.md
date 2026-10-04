---
id: ticketing-01
project: ticketing
source: "Punch List - Ticketing App Build Findings.md §1"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [contradiction, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Chapter 6: the until contract is stated wrongly, and the error shipped a real bug

**What happened.** The primer chapter says an `until` block resolves 'once the block returns a successful value.' In Reboot 1.4.1 the callable's shape is `Callable[[], Awaitable[bool | T]]` and only a literal `False` keeps the workflow waiting; any non-bool return resolves it, including `0.0` and `None`. The app's refund workflow, written to the chapter's description, returned `0.0` as its 'not approved yet' value: every refund bypassed manager approval and refunded $0.00. The code read correctly and passed a race-lenient test.

**Expected.** Show the wait callable returning `False` while waiting and the approved amount on success, state the `False`-only rule, and add a one-line warning ('never return a zero of the value type as the not-yet sentinel').

**Repro.** Not recorded.

**Where in the skills.** Primer Chapter 6 - Work Survives Interruption; the `servicer-workflow.md` skill carries the same truthy/None-sentinel claim (see team-memo-0826-01).

**Checked at 1.6.0.** python/references/servicer-workflow.md:1089-1092 and :1129-1137 still describe `until` as resolving on truthy and show `return response if response.settled else None  # None is falsy`.
