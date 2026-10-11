---
id: crm-kit-59
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §9"
reboot_version: 1.6.0
severity: unrated
target: positive
names:
  - python/references/servicer-writer.md
  - python/references/servicer-transaction.md
  - python/references/lifecycle-secrets.md
tags: [pattern]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-writer.md § When you are here; python/references/servicer-transaction.md § When you are here"
---

# Make external calls only inside workflows, under at_least_once; keep API keys in environment secrets

**What happened.** Writers and transactions are re-executed to validate effects, so memoized workflow steps are the only safe place for a side effect. API keys live in environment secrets, never in actor state.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `servicer-writer.md` and `servicer-transaction.md` (§ When you are here) send external calls to a workflow, as resolved for team-memo-0826-05; `lifecycle-secrets.md` covers secrets.
