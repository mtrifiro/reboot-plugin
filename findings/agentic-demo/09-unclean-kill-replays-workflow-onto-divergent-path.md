---
id: agentic-demo-09
project: agentic-demo
source: "v 1.4.1 Reboot/Archive/agentic-demo/docs/reboot-learnings.md §10"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [pattern, operations]
cluster: ""
duplicate_of: returns-desk-09
still_applies: yes
status: Open
resolved_by: ""
---

# After an unclean kill a workflow replayed onto a different path; drive post-commit phases from committed state

**What happened.** After a `kill -9` of the worker tree mid-demo (graceful Ctrl-C recovers cleanly), a resumed `ResolutionAttempt.Run` task replayed with different memoized step results than its original execution: an attempt whose committed resolution was REFUND replayed as REPLACE, then wedged forever retrying `mark_reservation_shipped` against a case with no reservation (undeclared abort, so infinite retry). The author's pattern: after a commit succeeds, the workflow drives its external-effect phase from the case's committed state (`committed_resolution`, `refund_amount_cents`), never from the local plan object a replay reconstructed. The wedged task drained itself as soon as the fixed code loaded: it re-read the committed REFUND and completed correctly.

**Expected.** Not recorded as a skill change. The divergent memoized results are a platform observation the source does not diagnose further.

**Repro.** `kill -9` the worker tree while workflows are mid-flight, then restart.

**Where in the skills.** `python/references/servicer-workflow.md` (no reference named by the source).

**Checked at 1.6.0.** grep for `kill -9`, SIGKILL, unclean and committed state finds only `run/references/stop-restart-reset.md` on SIGKILL orphaning processes; no workflow reference says to derive a post-commit phase from committed state rather than from replayed local values. agentic-demo's learnings file repeats returns-desk's text for this section (it is the same file with §11 added); see returns-desk-09.
