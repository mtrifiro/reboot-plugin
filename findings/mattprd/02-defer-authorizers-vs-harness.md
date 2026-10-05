---
id: mattprd-02
project: mattprd
source: "2026.08.22 REBOOT_FINDINGS.md §2"
reboot_version: 1.4.1
severity: yellow
target: plugin
names:
  - web-app/SKILL.md
  - python/references/servicer-authorizer.md
tags: [contradiction, error-text, testing, auth]
cluster: "4.1"
duplicate_of: theater-chain-04
still_applies: yes
status: Resolved
resolved_by: "web-app/SKILL.md § Auth in Web Apps; python/references/servicer-authorizer.md § Do this; python/references/auth-allow-deny.md § Do this; build/SKILL.md § Step 4 — Authorizers"
---

# Skill guidance conflict: 'defer authorizers in dev' vs the test harness enforcing them

**What happened.** The `web-app` skill's auth section says configure `oauth=OAuthProviderByEnvironment(dev=Development(), prod=None)`, omit `authorizer()`, and treat `rbt dev`'s 60-second warning as the TODO list. Its build-flow step 12 requires harness tests before running the app, and the `Reboot()` harness runs production-mode authorization, so a missing `authorizer()` means `PermissionDenied` for every external-context call: `Thread.SendMessageAborted: aborted with 'PermissionDenied': You are not authorized to call 'mattprd.v1.ThreadMethods.SendMessage' ...`. The failure does not explain why dev-mode-permitted calls are suddenly denied. `servicer-authorizer.md` says 'write rules from day one under `oauth=`', so the two references disagree.

**Expected.** Under `oauth=`, authorizers are written before the test step, full stop. Ideally the harness's PermissionDenied for a servicer with no authorizer says 'this Servicer defines no authorizer(); the test harness runs production-mode auth'.

**Repro.** Not recorded.

**Where in the skills.** web-app SKILL.md auth section vs build step 12; `servicer-authorizer.md`.

**Checked at 1.6.0.** web-app/SKILL.md:108-111 and python/references/servicer-authorizer.md:64-66 still say to omit `authorizer()` early; python/references/testing-harness.md:124 states production-mode authorization in tests. The web-app flow still does not reconcile the two.
