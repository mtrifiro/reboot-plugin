---
id: reboot-crm-40
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.7"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/lifecycle-secrets.md
  - python/references/lifecycle-reboot-cloud.md
  - deploy/SKILL.md
tags: [operations, auth, error-text, negative-space]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/lifecycle-secrets.md § Limits; deploy/SKILL.md § Step 2 — Deploy the backend to Reboot Cloud"
---

# Secrets cannot be set before an application exists, but some apps cannot start without them

**What happened.** The recommended production auth setup is `OAuthProviderByEnvironment(dev=Development(), prod=Google(client_id=..., client_secret=...))` with credentials as Cloud secrets. `rbt cloud secret set GOOGLE_OAUTH_CLIENT_ID GOOGLE_OAUTH_CLIENT_SECRET --application-name=... --organization=...` before the first deploy fails with "Organization '...' does not have an application named '...'". So `rbt cloud up` must come first, but `Google(...)` rejects a `None` `client_id` when the OAuth server mounts it, so the first-created application cannot start until secrets land in a later rollout; nothing says the first deploy is expected to be unhealthy. Scope established 2026-09-23: this bites only on creation. Secrets survive `rbt cloud down --expunge` (all seven were still set; the next `cloud up` came back healthy), and `rbt cloud secret list` answers while the app is down, so the application record and secret store outlive its state. Nothing in `lifecycle-secrets.md` or `lifecycle-reboot-cloud.md` says either way.

**Expected.** Fixes proposed: let `secret set` pre-seed a not-yet-existing application, or take secrets inline on first `cloud up`; skill fix: `lifecycle-secrets.md` and `deploy/SKILL.md` Step 2 state the ordering constraint and its consequence, and that `down --expunge` expunges state and keeps secrets. Recommendation: (1) pre-seed in the platform, (3) the docs today.

**Repro.** New application with a `prod=Google(...)` provider reading credentials from the environment; run `rbt cloud secret set` before `rbt cloud up`.

**Where in the skills.** `python/references/lifecycle-secrets.md`, `python/references/lifecycle-reboot-cloud.md`, `deploy/SKILL.md` Step 2.

**Checked at 1.6.0.** `lifecycle-secrets.md` (~lines 82-97) and `lifecycle-reboot-cloud.md` (~lines 101-130) give the `secret set` command but no ordering constraint, no first-rollout-unhealthy note and no `down --expunge` secret retention note (grep).
