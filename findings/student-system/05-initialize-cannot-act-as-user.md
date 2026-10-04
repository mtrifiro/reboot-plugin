---
id: student-system-05
project: student-system
source: "student-system/reboot-findings.md §5"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-initialize-hook.md
  - python/references/auth-allow-if.md
tags: [seeding, auth, negative-space]
cluster: "C"
still_applies: yes
status: Resolved
resolved_by: "python/references/lifecycle-initialize-hook.md § Never"
---

# No way for initialize to act as a particular user, so segregation of duties needed an app-internal exemption

**What happened.** The seed (`backend/src/seed.py`) runs from the `initialize` hook, which carries no `auth`, so every audit event it writes is attributed to `"system"` and every call is app-internal. The curriculum workflow requires the approver not be the proposer; with one "system" actor the seed could never publish a program. The app's fix: `Program.approve` skips the check when `context.app_internal` is true, with a comment. Human registrars remain bound. The author calls this a policy hole opened by the framework's shape.

**Expected.** Either an impersonation option for `InitializeContext` (`as_user=...`) or explicit guidance in `lifecycle-initialize-hook.md` that seeds are always the application, never a user, so workflows with person-level rules need an app-internal exemption.

**Repro.** Not recorded.

**Where in the skills.** `python/references/lifecycle-initialize-hook.md`.

**Checked at 1.6.0.** `python/references/lifecycle-initialize-hook.md` has no mention of `app_internal`, of the missing auth, or of attribution of seed calls.
