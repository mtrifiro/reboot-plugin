---
id: restaurant-app-3-05
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Plugin skills, item 2"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/auth-custom-predicates.md
tags: [auth, negative-space, pattern]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "python/references/auth-roles.md § Do this"
---
# No pattern for a staff roster: roles, invitations, the first admin

**What happened.** The skills give roles one sentence (`auth-custom-predicates.md` § Roles: "the roster's reader returns each member's roles, and the predicate checks the one the method needs"). Three apps built from the same skills each invented the rest differently. Lookup: `member_for_user` (this app; app-internal only; returns the whole entry), `who_is` (restaurant-app-2; self only), `role_of` / `my_role` (reboot-crm; any teammate). Keyed by: email with the sign-in id linked later (this app), email plus a reverse index from sign-in id (app-2), sign-in id with invitations as `invited:<email>` (reboot-crm). Verified email checked: no, no, yes. Asked on: every protected call, every protected call, admin methods only (entry is a separate allowlist check on the caller's own `User`). First admin: first sign-in wins, unguarded in production (this app); an email from an env var (app-2); first to register behind a deploy allowlist, refusing to start without one and repairing a missing superadmin on boot (reboot-crm). The developer called this app's method name "a horrible name for a method".

**Expected.** One reference (`auth-roles.md`) with the worked shape: roles on one roster actor and nowhere else, with why a copy on `User` is the wrong shortcut (no method on `User` writes a role, so nobody promotes themselves); the names `my_role` (the caller) and `role_of(user_id)` (predicates), each returning role and display name; two gates, access ("may you get in", an allowlist on the caller's own `User`) and role ("what may you do", read from the roster only where needed), with the per-call cost of each; invitations by verified email that keep their place (reboot-crm's invitation id plus owner alias); choosing the first admin safely (deploy allowlist or starting-admin email, refuse to boot in production without one, a boot-time repair); one worked feature file (the first admin, an invited host, a stranger refused, the last admin protected). reboot-crm's `servicers/auth.py` and `Team.register` are close to a ready-made source.

**Repro.** Any brief that says "staff sign in with roles".

**Where in the skills.** none; nearest is `python/references/auth-custom-predicates.md` § Roles. Cost here: one extra roster read on every call, live subscriptions included, plus a design round-trip with the developer.

**Resolution (2026-10-10).** A new conditional reference, `auth-roles.md` (when staff sign in with roles): one roster actor, `my_role` and `role_of`, the access and role gates and their cost, invitations adopted on a verified email, the first admin from an allowlist with the boot refusal and the repair, and a feature file; `auth-custom-predicates.md` and the build skill's design phase point at it.
