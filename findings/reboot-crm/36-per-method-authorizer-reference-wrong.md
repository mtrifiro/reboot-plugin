---
id: reboot-crm-36
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.3"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/servicer-authorizer.md
  - python/references/auth-custom-predicates.md
tags: [contradiction, auth, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# servicer-authorizer.md says per-method rules need a custom subclass; the generated <Type>.Authorizer already takes one rule per method

**What happened.** The author built a design (roles on a separate `Team` type, admin checks in method bodies) on the reference's statement that `def authorizer(self)` returns a single rule for every method and per-method differentiation "requires a custom authorizer subclass". Reading the generated code later, every type has a `<Type>Authorizer` (exposed as `<Type>.Authorizer`) whose constructor takes a rule per method (`Team.Authorizer(register=INTERNAL, ensure_superadmin=INTERNAL, _default=TEAMMATE)`), and a bare rule returned from `authorizer()` is wrapped as `<Type>Authorizer(_default=rule)`.

**Expected.** Rewrite the "Per-Method Authorization" sections of `servicer-authorizer.md` and `auth-custom-predicates.md` to lead with `<Type>.Authorizer(method_a=rule, method_b=rule, _default=rule)`, include the discovery command, and delete the claim that a custom subclass is required. Documentation only; the source ranks it above the rest of P3 and calls it the direct fix for reboot-crm-01. See also reboot-air-150-13 and student-system-06.

**Repro.** `grep -n "class .*Authorizer(" backend/api/<pkg>/v1/<name>_rbt.py` in any generated app.

**Where in the skills.** `python/references/servicer-authorizer.md` (~line 136), `python/references/auth-custom-predicates.md` (~line 199).

**Checked at 1.6.0.** `servicer-authorizer.md` lines 136-137 still say per-method differentiation "requires a custom authorizer subclass"; `auth-custom-predicates.md` lines ~199-205 still say to return a custom subclass.
