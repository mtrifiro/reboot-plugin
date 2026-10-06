---
id: constellation-08
project: constellation
source: "v 1.4.1 Reboot/constellation/docs/reboot-learnings.md §2026-08-16 — initial build"
reboot_version: 1.4.0
severity: unrated
target: positive
names:
  - python/references/servicer-writer.md
tags: [pattern]
cluster: ""
still_applies: unknown
status: Resolved
resolved_by: "python/references/servicer-writer.md § Do this"
---

# A pure-compute writer can gather cross-actor reads; no workflow needed

**What happened.** `recompute_edges` is a plain `Writer` that `asyncio.gather`s `Video.get` readers and computes TF-IDF cosine similarity locally; no workflow is needed because nothing leaves the system. Keep the math deterministic (sorted iteration, stable tie-breaks) "or dev-mode effect validation will flag it".

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/servicer-writer.md` § Do this: a writer may call readers on other actors. Its § Limits says effect validation reruns the body and "the runs are never compared" (1.6.0 source), which disagrees with the source's claim that nondeterministic math would be flagged; determinism still matters for the persisted result.
