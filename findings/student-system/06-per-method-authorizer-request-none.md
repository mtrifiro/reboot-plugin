---
id: student-system-06
project: student-system
source: "student-system/reboot-findings.md §6"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/auth-custom-predicates.md
  - python/references/servicer-authorizer.md
tags: [negative-space, auth, contradiction]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Per-method authorization by isinstance(request, ...) cannot express rules for methods with request=None

**What happened.** Following `auth-custom-predicates.md` (gate methods with a custom predicate that inspects the request type, rather than the `Type.Authorizer(method=rule, ...)` form docs.reboot.dev shows; see reboot-air-13), `common.role_authorizer` maps request classes to allowed roles with a `None` key as the default. A method declared with `request=None` has no request class to match, so it only gets the default rule: `GraduationApplication.begin_review` (`request=None`) fell under the default (any staff or the owning student) though only the registrar should advance an application. Methods that share a request model (`CourseAttempt.drop` and `withdraw` both take `AttemptReasonRequest`) cannot be given different rules. Readers with no request are fine under the default, so it went unnoticed. The author planned to switch to the documented per-method `Authorizer(...)` constructor.

**Expected.** The plugin reference should show the per-method `Authorizer(...)` form first.

**Repro.** Not recorded.

**Where in the skills.** `python/references/auth-custom-predicates.md` ("Per-Method Authorization").

**Checked at 1.6.0.** `python/references/auth-custom-predicates.md` (line ~136) still teaches narrowing with `isinstance(request, ...)`; no reference under `python/references/` shows the `<Type>.Authorizer(method=...)` constructor form (grep for `Authorizer(` found no hits).
