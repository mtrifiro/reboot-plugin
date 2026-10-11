---
id: team-memo-0826-05
project: team-memo-0826
source: "2026.08.26 Findings for Reboot Team - Docs, Skills, and Runtime.md §5"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-writer.md
  - python/references/servicer-transaction.md
  - python/references/patterns-common-gotchas.md
tags: [contradiction]
cluster: "8.4"
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-writer.md § When you are here; python/references/servicer-transaction.md § When you are here"
---

# Skills and docs give different rules for where external calls belong

**What happened.** Both agree a plain reader/writer/transaction must not perform an external side effect, but differ on where it goes. Public docs (side-effects page) say to isolate side effects in tasks, any method kind invocable as a task, with idempotent side effects: a scheduled writer sending an idempotent email is legal. Plugin skills are narrower: `servicer-writer.md` ('No external side effects in a writer, none, not even idempotent ones'; belongs in a Workflow), `servicer-transaction.md` ('if a call leaves the system, it belongs in a workflow, not a transaction'), and `patterns-common-gotchas.md` item 8. An agent building from docs and one building from skills produce different architectures; a reviewer cannot tell which is authoritative.

**Expected.** Either align the docs' page with the workflow-only rule, or state in the skills that 'workflow, not just any task' is a deliberate tightening of the public contract.

**Repro.** Not recorded.

**Where in the skills.** `servicer-writer.md`, `servicer-transaction.md`, `patterns-common-gotchas.md` item 8.

**Checked at 1.6.0.** python/references/servicer-writer.md:13 still reads 'external side effects in a writer — none, not even idempotent'; no `docs:` upstream-difference note found.
