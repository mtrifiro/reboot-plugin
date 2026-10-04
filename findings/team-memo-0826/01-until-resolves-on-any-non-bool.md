---
id: team-memo-0826-01
project: team-memo-0826
source: "2026.08.26 Findings for Reboot Team - Docs, Skills, and Runtime.md §1"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [contradiction, negative-space]
cluster: "4.1"
duplicate_of: reboot-crm-05
still_applies: yes
status: Open
resolved_by: ""
---

# until resolves on any non-bool value, not on truthiness

**What happened.** Workflow docs and the `servicer-workflow` skill describe `until` as re-evaluating until the callable returns a truthy value, and the skill's wait-for-value pattern returns `None` as the 'not yet' sentinel. Installed 1.4.1 only keeps waiting on a literal `False`; any non-`bool` return resolves immediately (`reboot/aio/contexts.py`, `retry_reactively_until`: `if not isinstance(result, bool): return result; elif result: return True`). Verified by source inspection, a live app (an `until` returning `0.0` resolved instantly, so a refund workflow bypassed manager approval and refunded $0.00), and a unit test where a `None` return resolved the wait.

**Expected.** Asks the team which side is the contract: if truthy-waiting is intended it is a runtime bug; if literal-`False` is intended, the docs, the skill's decision-aid text and its `None`-sentinel example need the corrected rule, with the signature presented as 'return `False` to keep waiting, `T` to resolve.'

**Repro.** A ten-line workflow whose `until` callable returns `0.0` (offered by the source).

**Where in the skills.** `servicer-workflow.md` (`until` section and wait-for-value pattern).

**Checked at 1.6.0.** python/references/servicer-workflow.md:1089-1137 still says 'Wait for a Condition to Become Truthy' and shows `return response if response.settled else None  # None is falsy`.
