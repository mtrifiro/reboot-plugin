---
id: reboot-crm-13
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.7"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [negative-space, error-text, version-drift]
cluster: "4.4"
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-workflow-wait.md § Never"
---

# An until result is memoized with its type, so changing the callable's return type poisons a running workflow forever

**What happened.** After finding reboot-crm-05, the callable was changed to return `bool`. The workflow already running could then never progress: every retry failed with `TypeError: Stored result of type 'str' from 'callable' is not compatible with the expected type 'bool' inferred ...`. The memo is keyed by alias and carries the type it was stored with, so fixing the callable does not fix a deployed workflow instance that already resolved the `until`; only a new alias (or an expunge) moves it on. `servicer-workflow.md` says "to wait again on a fresh condition, use a different alias", which is about waiting twice on purpose and does not warn that editing a callable's return type strands every instance that has run it. It took an hour; every fact needed was in the runtime's hands when it raised.

**Expected.** Say it in the reference beside the memoization note: changing an `until` callable's return type is a breaking change to in-flight workflows and the remedy is a new alias. A runtime hint in the error ("this alias stored a `str`; rename the alias to wait afresh") would turn an hour into a minute. Source recommends both.

**Repro.** Run a workflow past an `until` whose callable returns `str`; change the callable to return `bool`; restart.

**Where in the skills.** `python/references/servicer-workflow.md` memoization note and `until` section (~line 1145).

**Checked at 1.6.0.** `servicer-workflow.md` line ~1145 still has only "to wait again on a fresh condition, use a different alias"; nothing about return-type changes (grep for `return type` finds only the annotation advice).
