---
id: reboot-air-141-20
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §21"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/SKILL.md
tags: [auth, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Provider table says Development takes no claims= but it does

**What happened.** `web-app/SKILL.md` presents OAuth providers as a table of required arguments, then says the registered providers ("everything but `Development` and `Anonymous`") also take `scopes=`, `claims=`, and `store_tokens=`. Read plainly, `Development()` cannot take `claims=`; the author believed it, added a `set_claims` override, signed in, saw no log line or claims, and concluded the dev provider does not deliver identity. The booking page grew a form asking the signed-in user to retype their own name and email, which the user rejected twice, pointing out that name and email appear on the login screen. The installed class shows `Development.__init__(self, *, access_token_ttl_seconds=..., claims=None)` with `_AVAILABLE_CLAIMS = {"email", "email_verified", "name"}`; `Development(claims=["email", "name"])` makes `set_claims` fire with `{'email': 'alice@example.com', 'name': 'Alice'}`. Two defects: the table is wrong, and claims are opt-in with no warning: without `claims=` the app sees only an opaque `dev-{hash}`, `set_claims` is never called, with no error, startup warning, or log line.

**Expected.** Fix the table ("everything but `Anonymous`", list `claims=` on `Development`) and add "without `claims=`, the app receives only an opaque user id and `set_claims` is never called." Suggested framework changes: default `Development()` to `claims=["email", "name"]`; warn at startup when a servicer overrides `set_claims` but the provider requests no claims.

**Repro.** `Application(oauth=...Development())` with a servicer overriding `set_claims`; sign in; `set_claims` never fires. Add `claims=["email", "name"]` and it fires.

**Where in the skills.** `web-app/SKILL.md`, OAuth provider table ("Auth in Web Apps").

**Checked at 1.6.0.** Still present. `web-app/SKILL.md:127,134-135` still lists `Development()` as taking no arguments and excludes it from `claims=`; lines 139-140 still frame `claims=` as an enhancement.
