---
id: reboot-crm-05
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P0.5"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [contradiction, negative-space, error-text]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# until resolves on any non-bool result, whatever its truthiness; the reference's own example relies on the opposite

**What happened.** A consumer loop followed `servicer-workflow.md`'s "`until` — Wait for a Condition to Become Truthy": a callable reading `state.research_queue_id` (`""` until an import sets it), used as `Queue.ref(await until("The research queue", context, queue_id))`. It did not wait: `until` returned `""` immediately and the workflow died on `InvalidStateRefError: the 'state_id' option must be at least 1 character(s) long`, retrying forever. Cause in `contexts.py::retry_reactively_until`: `if not isinstance(result, bool): return result  # any non-bool resolves the wait`, `elif result: return True`, so only a `bool` is tested for truth; `""`, `0`, `None` resolve the wait on the first call. The reference's own example has the bug: `get_settled` returns `Optional[Order.GetResponse]` with the comment "None is falsy"; `None` is not a bool, so that wait resolves immediately.

**Expected.** Either the truthiness the prose promises ("reactively re-runs `callable` until it returns a truthy value") or prose saying a non-bool return resolves immediately. Source fix options: (1) honour truthiness for every type (recommended, a behaviour change); (2) raise on a falsy non-bool return; (3) fix the `get_settled` example in `servicer-workflow.md`, which must ship in the same release either way.

**Repro.** Wait with `until` on a callable returning `""` (or `0`/`None`) while the state is not yet set.

**Where in the skills.** `python/references/servicer-workflow.md` (`until` section, `get_settled` example).

**Checked at 1.6.0.** `python/references/servicer-workflow.md` lines ~1129-1139 still say `until` returns the truthy value, "anything truthy works", and keep the `get_settled` example with `# None is falsy`.
