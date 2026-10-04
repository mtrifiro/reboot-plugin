---
id: reboot-air-150-14
project: reboot-air-150
source: "reboot-air/reboot-findings.md §14"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-initialize-hook.md
  - python/references/rpc-refs.md
tags: [contradiction, negative-space]
cluster: "8.4"
still_applies: yes
status: Open
resolved_by: ""
---

# Two more places the plugin references disagree with docs.reboot.dev (constructors, readers on unconstructed state)

**What happened.** (1) Constructors: `lifecycle-initialize-hook.md` says "Constructors — `Service.create(context, id)` / factory methods — are a no-op on existing actors." The docs say "You can only call an explicit constructor once! Otherwise you'll get back a `StateAlreadyConstructed` error", with `.idempotently()` as the documented way to make construction safe to repeat. (The app avoided the question by probing with a reader first, which surfaced reboot-air-02.) (2) Readers on unconstructed state: `rpc-refs.md` says a reader "returns the zero-valued state"; the docs say "A state will not be implicitly constructed when you call a reader method", consistent with the `StateNotConstructed` abort observed. The docs are right; the reference is not.

**Expected.** Plugin references should match docs.reboot.dev.

**Repro.** Not recorded.

**Where in the skills.** `python/references/lifecycle-initialize-hook.md` (callout lines ~13-14) and `python/references/rpc-refs.md`.

**Checked at 1.6.0.** `lifecycle-initialize-hook.md` line 13 still says constructors are a no-op on existing actors (the callout does say `.idempotently` is needed for repeat calls); `rpc-refs.md` line ~105 still says zero-valued state.
