---
id: crm-kit-30
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §4"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/auth-allow-if.md
  - python/references/servicer-authorizer.md
tags: [auth, frontend]
cluster: "4.1"
duplicate_of: reboot-crm-44
still_applies: no
status: Resolved
resolved_by: "python/references/auth-allow-if.md § Never; python/references/servicer-authorizer.md § Never"
---

# With is_app_internal in allow_if(any=[...]), anonymous callers get PermissionDenied; treat it as go to sign-in

**What happened.** With `is_app_internal` in `allow_if(any=[...])`, an anonymous caller gets `PermissionDenied`, not `Unauthenticated`, because any `PermissionDenied` wins the aggregate. The frontend treats `PermissionDenied` as "go to sign-in".

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `servicer-authorizer.md` § Never and `auth-allow-if.md` § Never say anonymous callers get `PermissionDenied` from that rule.
