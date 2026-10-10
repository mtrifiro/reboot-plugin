---
id: crm-kit-74
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §11 Where this kit deliberately overrides a plugin skill"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - mcp-ui/references/api-state-shapes.md
  - python/references/state-actor-decomposition.md
tags: [contradiction, builder-drift]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "mcp-ui/references/api-state-shapes.md § Do this; python/references/state-actor-decomposition.md § Never"
---

# The builder skill says to hydrate nested models in the parent's factory create Writer; the factory should be a Transaction

**What happened.** `web-app/SKILL.md` (state shape) said to hydrate nested models "in the parent's factory `create` Writer". The kit declares every factory `Transaction(mode=Exclusive(), factory=True)` (§2) and hydrates there, because a constructor can't change kind once state exists.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `web-app/SKILL.md` (state shape), per the source.

**Checked at 1.6.0.** `web-app/SKILL.md` no longer says it, but `mcp-ui/references/api-state-shapes.md` (impactDescription and § "Single nested sub-object: hydrate in factory `create`") still says nested models are "hydrated in the factory `create` Writer", while `state-actor-decomposition.md` § Never says to start such constructors as `Transaction(mode=Exclusive(), factory=True)`.

**Resolution (2026-10-10).** `api-state-shapes.md` now declares the factory `create` a `Transaction(mode=Exclusive(), factory=True)` and says why, matching `state-actor-decomposition.md`.
