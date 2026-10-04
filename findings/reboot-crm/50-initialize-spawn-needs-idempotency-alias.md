---
id: reboot-crm-50
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.14"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/stdlib-queue.md
  - python/references/lifecycle-initialize-hook.md
tags: [seeding, error-text, pattern]
cluster: "C"
still_applies: yes
status: Open
resolved_by: ""
---

# Spawning from initialize needs an idempotency alias, which the consumer-loop example omits

**What happened.** `stdlib-queue.md` says to set up the consume loop "started from `initialize` or a transaction". Doing so fails with `IdempotencyRequiredError: calls to mutators from within your initialize function must use idempotency`. The fix is `.idempotently(alias=...)` before `.spawn()`, which is also what stops every boot starting another consumer beside the last one (a silent doubling of whatever the loop paces, here paid research calls).

**Expected.** Add `.idempotently(alias=...)` to the consumer-loop example in `stdlib-queue.md` with one sentence on why.

**Repro.** Not recorded.

**Where in the skills.** `python/references/stdlib-queue.md` (consumer-loop example).

**Checked at 1.6.0.** `stdlib-queue.md` has no `.idempotently` or `.spawn` text (grep); `lifecycle-initialize-hook.md` covers alias use in general.
