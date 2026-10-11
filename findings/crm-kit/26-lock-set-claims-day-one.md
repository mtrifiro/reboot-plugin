---
id: crm-kit-26
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §4"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/auth-claims.md
  - mcp-ui/references/auth-oauth-providers.md
tags: [auth]
cluster: "4.1"
duplicate_of: reboot-crm-01
still_applies: no
status: Resolved
resolved_by: "python/references/auth-claims.md § Limits"
---

# Lock set_claims on day one, or a signed-in user can forge a verified email

**What happened.** Under the default `User` rule, a signed-in user can call `set_claims` from the browser and write any `email`, forging every allowlist or "verified" badge built on the claim. Fix: `User.Authorizer(set_claims=allow_if(all=[is_app_internal]), _default=...)`. §11: `mcp-ui/references/auth-oauth-providers.md`, the auth page the `web-app` skill points to, teaches `claims=` without locking `set_claims`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `mcp-ui/references/auth-oauth-providers.md` (§11).

**Checked at 1.6.0.** `python/references/auth-claims.md` § Limits per the canonical item; `servicer-authorizer.md` § Limits now states `User.set_claims` is app-internal only, checked before any authorizer, which disagrees with what the source observed.
