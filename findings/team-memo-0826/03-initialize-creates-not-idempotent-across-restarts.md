---
id: team-memo-0826-03
project: team-memo-0826
source: "2026.08.26 Findings for Reboot Team - Docs, Skills, and Runtime.md §3"
reboot_version: 1.4.1
severity: unrated
target: framework
names:
  - python/references/lifecycle-initialize-hook.md
  - python/references/servicer-constructor.md
tags: [seeding, error-text]
cluster: "C"
still_applies: unknown
status: Resolved
resolved_by: "python/references/lifecycle-initialize-hook.md § Errors you will see"
---

# initialize-hook creates are not idempotent across every restart

**What happened.** `lifecycle-initialize-hook` and `servicer-constructor` skills say `Service.create(context, id)` is idempotent from `initialize` and safe on every start. After an ordinary `rbt dev run` restart with persisted state (no expunge), the `Event.create` factory transaction failed with `StateAlreadyConstructed` and the hook retried forever; the log named a different application id than earlier boots. The app now guards the seed with read-then-create and catches both aborts. Caveat in source: the machine had earlier accumulated orphaned server generations (§4), though the failure recurred after those were killed.

**Expected.** Source asks under what conditions the initialize idempotency scope stops covering a prior boot's create, and whether the per-boot application id in that log line is expected to change under a fixed `--application-name`.

**Repro.** Not recorded.

**Where in the skills.** `lifecycle-initialize-hook.md`, `servicer-constructor.md`, `rpc-constructor-calls.md`.

**Resolution (2026-10-10).** `lifecycle-initialize-hook.md` § Errors you will see: the `Transaction '<id>' missing` assertion from concurrent calls on one context (one call at a time, or a context per caller); the `StateAlreadyConstructed` row already covered a factory create after an ordinary restart.
