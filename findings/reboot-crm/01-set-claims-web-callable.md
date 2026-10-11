---
id: reboot-crm-01
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P0.1"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - mcp-ui/references/auth-oauth-providers.md
  - web-app/SKILL.md
tags: [auth, negative-space, index-gap]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/auth-claims.md § Limits"
---

# User.set_claims is web-callable under the default User rule

**What happened.** With `Google(claims=["email", "email_verified"])` the framework delivers verified claims to the generated `User.set_claims`. That is an ordinary method of the `User` type and the default `User` authorizer is `allow_if(any=[state_id_is_user_id, is_app_internal])`, so the signed-in user can call `set_claims` on their own actor from the browser and write any `email`. Anything that trusts the stored claim (a sign-in allowlist, a "verified email" display) is forgeable. The app closed it with `User.Authorizer(set_claims=allow_if(all=[is_app_internal]))`.

**Expected.** `set_claims` should default to app-internal only, whatever the type's rule; nothing legitimate calls it from outside. Failing that, `auth-oauth-providers.md` ("Identity claims") should say to lock it down. Fix options in the source: (1) runtime default, treated as a security release; (2) generated authorizer emits `set_claims=allow_if(all=[is_app_internal])`; (3) skill shows the lock-down line beside `claims=[...]`. The source recommends (1) and shipping (3) immediately; it also notes `auth-oauth-providers.md` exists only under `mcp-ui/references/`, so a Web App built from the `web-app` skill (whose only reference is `react-client.md`) has no auth page to carry the warning.

**Repro.** Any `User` type with `claims=` on the provider and no explicit `set_claims=` rule; call `set_claims` from the generated web client as the signed-in user.

**Where in the skills.** `mcp-ui/references/auth-oauth-providers.md` ("Identity claims"); `web-app/` has no auth reference.

**Checked at 1.6.0.** `mcp-ui/references/auth-oauth-providers.md` (lines ~72-96) shows an `set_claims` override but no lock-down rule (grep for `app_internal` found none in that file); `web-app/` still has only `references/react-client.md`.
