---
id: meridian-circuit-02
project: meridian-circuit
source: "v 1.4.1 Reboot/meridian-circuit/docs/2026.08.18 reboot-learnings porting supabase app.md §2"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow-calls.md
tags: [error-text]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-workflow-calls.md § Errors you will see; python/references/servicer-workflow-calls.md § Never"
---

# `.read()` on another actor's ref is rejected inside a Workflow, with a message that says the opposite

**What happened.** `state = await Chain.ref(CHAIN_ID).read(context)` in a `WorkflowContext` fails with ``RuntimeError: `read()` is currently only supported within workflows; Please reach out and let us know your use case if this is important for you!``, which is confusing because the call is in a workflow; the message appears inverted or narrower than it says. Fix: use the declared reader with an explicit workflow scope, `await Chain.ref(CHAIN_ID).per_workflow("directory").get(context)`; scoping is required anyway so a replay reuses the memoized result instead of re-reading live state.

**Expected.** Not recorded (the source reads the message as inverted).

**Repro.** Inline `.read(context)` on `Chain.ref(CHAIN_ID)` from inside a workflow.

**Where in the skills.** `python/references/servicer-workflow-calls.md` (This actor's state, Never, Errors).

**Checked at 1.6.0.** Documented: `servicer-workflow-calls.md` § This actor's state says inline `.read()` / `.write()` exist only on the no-arg `ref()` and another actor needs its declared Reader; § Never lists `Other.ref(id).read(context)`; § Errors you will see maps the exact message to 'Inline `read()` on a ref with an id'. The misleading wording itself is a runtime string.
