---
id: crm-kit-38
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §6"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/testing-project-setup.md
  - python/references/testing-features.md
tags: [testing, auth, scaffold]
cluster: "B"
duplicate_of: reboot-crm-55
still_applies: no
status: Resolved
resolved_by: "python/references/testing-project-setup.md § Errors you will see"
---

# Every harness needs an explicit OAuth with allowed_origins

**What happened.** The harness is neither `rbt dev run` nor `rbt serve`, so `OAuth` demands `allowed_origins`. Rule: `oauth=OAuth(provider=OAuthProviderByEnvironment(dev=d, prod=d), allowed_origins=[])`, with `[frontend.origin]` in browser modules. §11: `testing-features.md`'s minimal fixture lacks `oauth=`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `testing-features.md` (§11).

**Checked at 1.6.0.** `python/references/testing-project-setup.md` § Errors you will see, per the canonical item reboot-crm-55.
