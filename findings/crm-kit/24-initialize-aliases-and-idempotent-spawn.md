---
id: crm-kit-24
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §3"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/stdlib-queue.md
  - python/references/lifecycle-initialize-hook.md
tags: [error-text, pattern]
cluster: "C"
duplicate_of: reboot-crm-50
still_applies: no
status: Resolved
resolved_by: "python/references/stdlib-queue.md § Do this"
---

# In initialize, every call that must run again needs an alias naming what it acts on; spawns go through .idempotently(alias=...)

**What happened.** `initialize` calls are idempotent per actor and method for the application's life, and the keys survive expunge and restore. A bare call runs on the first boot only. A spawn without an alias raises `IdempotencyRequiredError`. Examples: `await pipeline.idempotently(alias=f"heat caches v{RULES_VERSION}").rebuild(context, version=RULES_VERSION)`; `await leads.idempotently(alias=f"research loop for {queue_id}").spawn().research_loop(context)`. §11: `stdlib-queue.md` says "started from `initialize`" without `.idempotently(alias=...)`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `stdlib-queue.md` (§11).

**Checked at 1.6.0.** `python/references/stdlib-queue.md` § Do this (canonical reboot-crm-50); `lifecycle-initialize-hook.md` (~104) says a bare call runs once in the application's lifetime; `errors.md` indexes `IdempotencyRequiredError`.
