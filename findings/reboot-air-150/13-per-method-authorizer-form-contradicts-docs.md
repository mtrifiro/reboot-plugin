---
id: reboot-air-150-13
project: reboot-air-150
source: "reboot-air/reboot-findings.md §13"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/auth-custom-predicates.md
tags: [contradiction, auth]
cluster: "8.4"
still_applies: yes
status: Open
resolved_by: ""
---

# Per-method authorizer rules are documented upstream, but the plugin's reference says they need a custom subclass

**What happened.** docs.reboot.dev/learn_more/auth shows the direct form: `def authorizer(self): return Account.Authorizer(balance=allow_if(any=[is_admin, is_account_owner]), deposit=allow(), withdraw=allow_if(all=[is_account_owner]))`. The plugin's `auth-custom-predicates.md` ("Per-Method Authorization") instead says to return a custom `Authorizer` subclass that inspects the request type or method name, and that "For most apps, splitting state into multiple Servicers with different authorizers is simpler than building a per-method rule." Following that, the app's `Flight` and `Order` authorizers dispatch on `isinstance(request, ...)` inside one predicate, which is harder to read and audit than the documented `<Type>.Authorizer(...)` form.

**Expected.** The reference should show the documented per-method constructor.

**Repro.** Not recorded.

**Where in the skills.** `python/references/auth-custom-predicates.md`, "Per-Method Authorization".

**Checked at 1.6.0.** `python/references/auth-custom-predicates.md` (line ~136) still teaches `isinstance(request, ...)` narrowing; no reference shows `<Type>.Authorizer(method=...)` (grep for `Authorizer(` found none).
