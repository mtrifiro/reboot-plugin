---
id: reboot-crm-44
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.8"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/auth-allow-if.md
  - web-app/SKILL.md
tags: [auth, contradiction, error-text]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/auth-allow-if.md § Never; python/references/servicer-authorizer.md § Never"
---

# allow_if(any=[is_app_internal, has_verified_token]) reports PermissionDenied to anonymous callers

**What happened.** An unauthenticated caller got `PermissionDenied`, not `Unauthenticated`. `auth-allow-if.md` documents the aggregation rule (any `PermissionDenied` wins) and `is_app_internal` returns `PermissionDenied` for an external caller, so the more useful `Unauthenticated` (which tells a client to sign in) is masked whenever `is_app_internal` is in the list, which is the pattern the skill itself recommends for web apps.

**Expected.** Fixes proposed: have `is_app_internal` fail as `Unauthenticated` for an external caller (preferred), or prefer `Unauthenticated` in aggregation; at minimum warn about the ordering in `auth-allow-if.md`.

**Repro.** Not recorded.

**Where in the skills.** `python/references/auth-allow-if.md` (aggregation rules, lines ~65-75), `web-app/SKILL.md` recommended pattern.

**Checked at 1.6.0.** `auth-allow-if.md` lines 72-75 still state the PermissionDenied-wins aggregation without a warning about `is_app_internal`.
