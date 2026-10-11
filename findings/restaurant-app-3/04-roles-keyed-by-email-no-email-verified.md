---
id: restaurant-app-3-04
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Plugin skills, item 1"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/auth-claims.md
  - python/references/auth-custom-predicates.md
tags: [auth, negative-space]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "python/references/auth-claims.md § Never"
---
# Roles keyed by email with no word about `email_verified`

**What happened.** Following `auth-claims.md` ("Key by the `email` claim; look up the user ID at runtime", line ~102), two independent builds of the same app (restaurant-app-2 and this one) linked a sign-in to a roster entry by email and never read `email_verified`. With a provider that issues unverified emails, anyone can sign in as a roster address they do not own and inherit its role. `Development()` only issues its own five fabricated addresses, so no dev run or scenario exposes it. reboot-crm gets it right: `Team.register` adopts an invitation only when the provider verified the address, and its comment says so.

**Expected.** The sentence that says to key by email should say in the same breath: request `email_verified` (`Development(claims=["email", "email_verified", "name"])`) and claim nothing on an unverified address; a Never ("link a sign-in to a roster entry, invitation or any email-keyed record unless `request.claims["email_verified"]` is true; an unverified address is a claim anybody can make"); and the check shown in the `set_claims` example itself, since agents copy examples.

**Repro.** Any `set_claims` that links `claims["email"]` to a roster entry without checking `claims["email_verified"]`.

**Where in the skills.** `python/references/auth-claims.md` (Do this; the claims table lists `email_verified` for every provider but nothing uses it; Never); `python/references/auth-custom-predicates.md` (Roles).

**Resolution (2026-10-10).** `auth-claims.md` requests `email_verified` in its Do-this example, checks it in the `set_claims` example, and its Never forbids linking an email-keyed record on an unverified address; `auth-roles.md` carries the roster shape and the feature file that proves the refusal; the `design-roles` eval gains an `email-verified` grader.
