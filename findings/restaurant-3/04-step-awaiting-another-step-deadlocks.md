---
id: restaurant-3-04
project: restaurant-3
source: "restaurant-3/FINDINGS.md § reboot.bdd, item 3"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-features.md
tags: [negative-space, testing]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# A decorated step that awaits another decorated step deadlocks

**What happened.** `_is_a_signed_in_server_assigned_to` awaited `_is_a_signed_in(...)`, another `@given` step; the run hung until pytest-timeout (300 s) and the stack showed `reboot/bdd/loop.py` `run_coroutine_threadsafe(...).result()` waiting on the loop it was called from. Factoring the body into a plain `async def` helper fixed it.

**Expected.** Either a step callable from another step, or a documented rule to share plain helpers.

**Repro.** Two `@given` async steps, one awaiting the other.

**Where in the skills.** `python/references/testing-features.md` ("Custom steps are plain Reboot code"): none.
