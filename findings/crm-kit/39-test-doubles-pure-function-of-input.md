---
id: crm-kit-39
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §6"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/testing-features.md
tags: [testing]
cluster: "D"
duplicate_of: reboot-crm-04
still_applies: no
status: Open
resolved_by: ""
---

# Make every test double for an external call a pure function of its input

**What happened.** The harness keeps effect validation on. An `at_least_once` callable runs twice and keeps the **second** result. A stub that pops answers off a list feeds step 2 to the re-run, and the workflow silently skips step 1. §11: `testing-features.md`'s only example is `assert send_email.call_count == 2`, wrong for paid calls and stateful stubs.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `testing-features.md` (§11).

**Checked at 1.6.0.** `python/references/testing-features.md` § Never: "A stand-in that answers from a counter or a popped list" ... "Derive the answer from the input"; the `call_count == 2` example remains in § Do this with a comment.
