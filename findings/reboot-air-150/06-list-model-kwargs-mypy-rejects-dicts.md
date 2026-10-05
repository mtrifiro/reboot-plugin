---
id: reboot-air-150-06
project: reboot-air-150
source: "reboot-air/reboot-findings.md §6"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/rpc-calls.md
tags: [negative-space, testing]
cluster: "8.4"
still_applies: yes
status: Resolved
resolved_by: "python/references/rpc-calls.md § Never"
---

# Kwargs typed as list[Model] reject plain dicts under mypy but accept them at runtime

**What happened.** `await user.checkout(ctx, passengers=[{"flight_id": ..., ...}])` runs fine (pydantic coerces), but `mypy` reports `List item 0 has incompatible type "dict[str, Any]"; expected "PassengerAssignment"`. The author notes it is not a bug.

**Expected.** `rpc-calls.md` could mention that nested request models must be constructed as the `Model` class from `api/<pkg>/v1/<name>.py` (not `<Type>.<Model>`, which does not exist for non-request/response models).

**Repro.** Not recorded.

**Where in the skills.** `python/references/rpc-calls.md`.

**Checked at 1.6.0.** `python/references/rpc-calls.md` has no note on constructing nested request models (grep for `list[` found none).
