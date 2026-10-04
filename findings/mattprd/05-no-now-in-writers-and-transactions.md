---
id: mattprd-05
project: mattprd
source: "2026.08.22 REBOOT_FINDINGS.md §5"
reboot_version: 1.4.1
severity: yellow
target: plugin
names:
  - python/references/servicer-workflow.md
  - python/references/state-collections.md
  - python/references/servicer-writer.md
tags: [contradiction, negative-space, pattern]
cluster: "E"
still_applies: yes
status: Open
resolved_by: ""
---

# No sanctioned 'now' in writers/transactions; timestamps must come from the client

**What happened.** Writer/transaction bodies re-execute under dev-mode effect validation, so `time.time()` inside one is nondeterministic. The workflow answer is documented (capture time in `at_least_once`) but writers and transactions have no equivalent and there is no `context.now()`. The only replay-safe options: thread a `now_ms` field through every mutating request from the browser (what the app did), which bloats the API and trusts client clocks, or ignore timestamps. Curiously, `str(uuid4())` inside constructors/transactions is the canonical pattern (`state-collections.md` allocates OrderedMap ids that way) and is equally nondeterministic, so the runtime evidently has a mechanism making fresh randomness safe that is not exposed or documented for time.

**Expected.** A deterministic `context.now()` on Writer/Transaction contexts (captured once per invocation, replayed on validation), and a reference section explaining why `uuid4()` in write bodies is safe under effect validation; builders currently follow the example on faith while workflow docs state the opposite rule.

**Repro.** Not recorded.

**Where in the skills.** `servicer-workflow.md` (workflow-only capture), `state-collections.md` (uuid4/uuid7 in write bodies).

**Checked at 1.6.0.** python/references/servicer-workflow.md:658-678 still documents only the workflow-side `at_least_once` capture and says there is no clock on the context; state-collections.md:188-222 still allocates ids with `uuid7()` in write bodies with no explanation.
