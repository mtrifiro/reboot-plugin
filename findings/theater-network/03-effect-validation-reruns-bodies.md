---
id: theater-network-03
project: theater-network
source: "theater-network/docs/reboot-findings.md §3"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/state-collections.md
  - python/references/servicer-writer.md
  - python/references/testing-failure-recovery.md
  - python/references/servicer-constructor.md
tags: [negative-space, contradiction, testing]
cluster: "4.1"
duplicate_of: student-system-08
still_applies: yes
status: Open
resolved_by: ""
---

# Effect validation re-runs bodies: uuid4 in a constructor fails, failures look like hangs

**What happened.** Dev-mode effect validation re-executes writer/transaction bodies and asserts the mutations are deterministic. Three consequences: (1) `uuid4()` in a constructor fails validation because the second run produces a different id; the fix was to derive stored ids from the actor's own id (`f"{self.ref().state_id}-seats"`). (2) A failing `initialize` is retried forever with backoff; under pytest output capture this looks like a hang and `pytest -s` shows the retry warnings. (3) Transactions overlapping in time can convoy under validation: a confirm racing its hold's expiry timer (both on the same cart) mutually starved at the 30s lock deadline with validation ON; with validation OFF the confirm proceeds and the timer's first attempt retries once. The test harness disables validation to match production semantics.

**Expected.** Not recorded.

**Repro.** A constructor that persists `uuid4()`; confirm racing an expiry timer on one cart with validation on.

**Where in the skills.** Contradicts `python/references/state-collections.md` (lines ~178 and ~205), which tells the agent to allocate an index id with `uuid4()` in the constructor. Also disagrees with the claim in cineloop-06 / cineloop-15 that validation aborts and retries rather than diffing; the two source projects differ on whether a differing persisted value fails validation.

**Checked at 1.6.0.** `state-collections.md` still recommends `self.state.<x>_index_id = str(uuid4())` in the constructor and `stdlib-ordered-map.md` shows the same; no skill says a non-deterministic constructor value fails validation, nor that a failing `initialize` looks like a hang under pytest. `testing-failure-recovery.md:168` mentions turning validation off for a test.
