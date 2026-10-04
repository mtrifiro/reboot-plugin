---
id: student-sor-01
project: student-sor
source: "student-sor/reboot-findings.md §1"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/patterns-idempotency.md
  - python/references/testing-harness.md
tags: [negative-space, error-text, testing, auth]
cluster: "4.1"
still_applies: unknown
status: Open
resolved_by: ""
---

# An authorization denial marks the caller's context as uncertain, and later mutations from it fail

**What happened.** A `PermissionDenied` from an authorizer is treated as uncertain. In the test suite, after asserting a student is denied `submit_grade`, the next mutation on the same context raised `reboot.aio.idempotency.IdempotencyUncertainError: Because we don't know if the mutation from calling 'sor.v1.PetitionMethods.Decide' of state 'PET-00001' failed or succeeded AND you've made some NON-IDEMPOTENT mutations we can't reliably determine whether or not the call to 'sor.v1.CourseAttemptMethods.SubmitGrade' ... is due to a retry`. The denial happened before the method body ran, so there is nothing to be uncertain about; the same applies to `Unauthenticated`. Workaround: tests use a throwaway context for every call expected to be denied (`fresh()` in `backend/tests/sor_test.py`). Frontend code is unaffected because the browser client mints idempotency keys.

**Expected.** `patterns-idempotency.md` says a call that aborts with an error "definitively from the backend" creates no uncertainty, and only transport failures or undeclared errors do. Suggestion: treat authorizer decisions as definitive, and mention this in `testing-harness.md` next to the negative-auth example, which as written will hit it.

**Repro.** Not recorded.

**Where in the skills.** `python/references/patterns-idempotency.md` (Uncertain Mutations); `python/references/testing-harness.md` negative-auth example.

**Checked at 1.6.0.** `python/references/patterns-idempotency.md` (lines ~76-110) still states only declared errors are safe and does not mention authorizer denials; `testing-harness.md` was not found to warn about it. Behaviour is consistent with the documented rule (denial is undeclared), so whether the framework should change is unresolved.
