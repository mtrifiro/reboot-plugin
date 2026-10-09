---
id: crm-kit-58
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §9"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow-external.md
  - python/references/testing-failure-recovery.md
tags: [cost, negative-space]
cluster: "D"
duplicate_of: reboot-crm-04
still_applies: no
status: Open
resolved_by: ""
---

# Pass effect_validation=EffectValidation.DISABLED to every at_least_once that wraps a paid call

**What happened.** In dev and in the harness, `at_least_once` calls the callable twice and keeps the second result, so every paid call bills twice (107 imports made 214 paid calls). No claim or cooldown in the workflow can stop it, because both calls happen inside one `at_least_once` before commit. Don't disable validation app-wide in `.rbtrc`; it keeps checking everything else for free. Shape: `from reboot.aio.contexts import EffectValidation`; `answer = await at_least_once("Ask the model", context, ask, effect_validation=EffectValidation.DISABLED)`. §11: no reference showed `effect_validation=` on `at_least_once` (`testing-failure-recovery.md` had only the harness-wide switch).

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `testing-failure-recovery.md` (§11).

**Checked at 1.6.0.** `servicer-workflow-external.md` § Limits (line ~169) and `testing-failure-recovery.md` § Counting calls (line ~124) now give the per-call `at_least_once(..., effect_validation=EffectValidation.DISABLED)`; `errors.md` indexes the `Re-running block` log line with the same fix.
