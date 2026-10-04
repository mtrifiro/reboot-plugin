---
id: reboot-crm-32
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P2.3"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/rpc-forall.md
tags: [cost, negative-space]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# Fan-out reader first push is slow

**What happened.** `Pipeline.board` -> `Account.forall(47 ids).summary()` takes about 2.9 s to first push in dev (twice that work with effect validation). Later pushes are incremental. Not a bug, but there is no stated expectation for transitive-query latency or whether the server batches `forall` inside a reactive context.

**Expected.** Fix proposed: document the expected latency in `python/references/rpc-forall.md` (a first push over ~50 actors costs seconds, doubled under effect validation, later pushes incremental); batch `forall` inside a reactive context if the runtime does not already. Recommendation: the documentation now.

**Repro.** Not recorded.

**Where in the skills.** `python/references/rpc-forall.md`.

**Checked at 1.6.0.** `rpc-forall.md` mentions batching internally (lines ~12-25) but gives no latency expectation (grep).
