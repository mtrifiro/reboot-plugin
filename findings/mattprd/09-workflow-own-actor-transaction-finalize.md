---
id: mattprd-09
project: mattprd
source: "2026.08.22 REBOOT_FINDINGS.md §9"
reboot_version: 1.4.1
severity: green
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [pattern, negative-space]
cluster: "E"
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-workflow-calls.md § Do this"
---

# Undocumented but load-bearing: workflow -> own-actor transaction for idempotent multi-actor finalization

**What happened.** The `respond` workflow must atomically create a `Document` (+ first `DocumentVersion`), append its id to the thread's state, index it on the `User`, create an assistant `Message`, and clear a `responding` flag. As separate workflow steps this risks replay-created duplicates (constructor calls with auto-generated ids are not naturally idempotent from a workflow body). What worked: a `finalize_response` Transaction on the workflow's own actor, called via `Thread.ref(context.state_id).per_workflow("Finalize").finalize_response(...)`: one memoized Reboot call, atomic, replays return the cached result. The references never show a workflow calling a declared method on its own actor, so it was used on inference. The authorizer rule `allow_if(any=[<owner>, is_app_internal])` covers it.

**Expected.** Bless and document in `servicer-workflow.md` as the canonical 'workflow needs to create actors and mutate several states atomically' recipe, and confirm semantics (no deadlock between a workflow and a transaction on the same actor).

**Repro.** Not recorded.

**Where in the skills.** `servicer-workflow.md`.

**Checked at 1.6.0.** grep for `state_id).per_workflow`/'own actor'/'same actor' in python/references/servicer-workflow.md finds no such recipe.
