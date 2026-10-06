---
id: crm-kit-25
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §3"
reboot_version: 1.6.0
severity: unrated
target: framework
names:
  - python/references/testing-harness.md
tags: [error-text, testing]
cluster: "4.4"
duplicate_of: reboot-crm-27
still_applies: no
status: Resolved
resolved_by: "python/references/testing-harness.md § Errors you will see"
---

# Keep one shared servicer list for main.py and every harness; a missing type fails at call time with Method not found!

**What happened.** A type missing from `Application(servicers=[...])` boots cleanly, then fails at call time with `UNIMPLEMENTED: Method not found!`, the same text as a harness race. Stdlib types also need `queue.servicers()` and `libraries=[ordered_map_library(), sorted_map_library()]`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/testing-harness.md` § Limits and § Errors you will see cover the missing servicer; `queue.servicers()` and `sorted_map_library()` were not found under `skills/` (grep).
