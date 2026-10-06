---
id: returns-desk-05
project: returns-desk
source: "v 1.4.1 Reboot/Archive/returns-desk/docs/reboot-learnings.md §7"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [negative-space, testing]
cluster: "D"
duplicate_of: reboot-crm-04
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-workflow-external.md § Limits"
---

# Effect validation re-fires at_least_once external callables in workflows, and the re-run's result wins

**What happened.** Repro in `backend/tests/refund_timeout_test.py` (harness, default effect validation): a workflow makes an external POST inside `at_least_once("Provider refund call 1", ...)`; the provider is armed `COMMIT_THEN_TIMEOUT_ONCE`, so the first invocation commits server-side and the client times out (the callable returns `UNKNOWN` as data, it never raises). The simulator's log shows two POSTs with the same idempotency key, while the persisted workflow path shows one provider attempt: the timeline jumps from `Payment refund requested (HTTP attempt 1)` straight to `Payment result reconciled` (the second POST's `created=false` response), and every `per_workflow` write before the step stayed single-execution. The author's reading: the validation pass re-invoked the callable instead of returning the memoized result, and the re-execution's outcome won. Consequences: the docs' claim that `at_least_once` memoizes the first result is not true under effect validation, so stable idempotency keys are load-bearing for every external call, not just retries (the stable key is why the ledger still held exactly one refund; only the attempt counter lied); invocation counters derived from workflow steps (`provider_attempt_count`) are nondeterministic. The test was fixed with `effect_validation=EffectValidation.DISABLED`; the UI treats the provider ledger's own `http_attempts` as authoritative.

**Expected.** A warning box in `servicer-workflow.md`'s `at_least_once` section about effect validation re-firing externals in dev/test, mirroring the existing writer/transaction warning.

**Repro.** `backend/tests/refund_timeout_test.py`: an external POST in `at_least_once` against a provider that commits then times out once; count POSTs at the provider.

**Where in the skills.** `python/references/servicer-workflow.md` (`at_least_once` section).

**Checked at 1.6.0.** `python/references/servicer-workflow-external.md` § Limits now says effect validation runs an `at_least_once` callable twice in development and the test harness and memoizes the second result, with the per-call `effect_validation=EffectValidation.DISABLED` opt-out; § Never warns against list-popping test stand-ins; `errors.md` has the `Re-running block with idempotency alias` row. Same gap as reboot-crm-04.
