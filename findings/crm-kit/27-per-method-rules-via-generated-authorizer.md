---
id: crm-kit-27
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §4"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/servicer-authorizer.md
  - python/references/auth-custom-predicates.md
tags: [auth]
cluster: "4.1"
duplicate_of: reboot-crm-36
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-authorizer.md § Do this; python/references/auth-custom-predicates.md § Do this"
---

# Gate per method with the generated <Type>.Authorizer(method=rule, ..., _default=rule); no custom subclass

**What happened.** Every type already takes one rule per method (snake_case keyword); a bare rule becomes `_default`. Believing this needs a "custom subclass" (as `servicer-authorizer.md` said, §11) cost a whole design. Check with `grep -n "class .*Authorizer(" backend/api/<pkg>/v1/<pkg>_rbt.py`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `servicer-authorizer.md` (§11).

**Checked at 1.6.0.** `servicer-authorizer.md` § Limits says per-method rules go in `<Type>.Authorizer(...)`; `auth-custom-predicates.md` § Never forbids a custom subclass for this.
