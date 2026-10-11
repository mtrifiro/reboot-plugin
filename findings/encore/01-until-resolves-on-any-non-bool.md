---
id: encore-01
project: encore
source: "v 1.4.1 Reboot/encore/docs/reboot-learnings 02.md §1"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [contradiction, negative-space]
cluster: "4.1"
duplicate_of: reboot-crm-05
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-workflow-wait.md § Never"
---

# until resolves on any non-bool result, "" included

**What happened.** `reboot.aio.workflows.until` keeps waiting only while the callable returns a literal `False`; any non-bool return resolves the wait at once, falsy ones too (`""`, `0`, and, contrary to the skill reference's `Optional` example, `None`), per `contexts.py:1530`: `if not isinstance(result, bool): return result`. A callable shaped `return status if done else ""` resolved instantly with `""`, and a checkout workflow voided a successfully settled charge because `outcome` was `""`, not `"settled"`. The author's rule: return `False` while pending, the non-bool value when done, and pass `type=` explicitly since the return annotation is no longer a single type (`outcome = await until("Charge settled", context, charge_outcome, type=str)`).

**Expected.** Return `False` to keep waiting; the reference's `None` sentinel example is wrong.

**Repro.** An `until` callable that returns `""` while a `PaymentSim` charge is pending.

**Where in the skills.** `python/references/servicer-workflow.md` (`until` section and its `Optional` example).

**Checked at 1.6.0.** `python/references/servicer-workflow-wait.md` § Do this ("`until`: return `False` to keep waiting") says any non-bool, `""` included, resolves, and § Never lists `return response if ready else None` (or `0`, `0.0`, `""`) as the mistake; its errors table carries the `""`-resolved symptom.
