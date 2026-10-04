---
id: cineloop-06
project: cineloop
source: "cineloop/reboot-findings.md §6 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/scheduling-recurring.md
  - python/references/servicer-writer.md
tags: [pattern, contradiction]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Wall-clock in a writer: when it is actually fine (observed vs addressed)

**What happened.** The scheduling reference warns against persisting a wall-clock or random value from a writer, which read literally forbids storing a hold deadline. Reading the runtime settled it: effect validation works by aborting and retrying the body (`EffectValidationRetry`), not by diffing the two runs' mutations; the first attempt's effects are discarded, so a timestamp differing by milliseconds is not an inconsistency. Rule: persisting a non-deterministic value from a writer is fine when the value is only observed; it is a bug when something else must re-derive or address it (an actor ID, idempotency key, foreign key). Workflows are different: replay must reproduce the same value (`at_least_once`-memoized now).

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Contradicts theater-network-03, which reports that `uuid4()` in a constructor fails effect validation because the second run produces a different id (a persisted, addressed value, so the two are compatible only under the observed-vs-addressed rule). Plugin fix is item 15 (scheduling-recurring warning too broad).
