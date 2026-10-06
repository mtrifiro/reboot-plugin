---
id: crm-kit-12
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §2"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/api-schema-evolution.md
  - mcp-ui/references/auth-oauth-providers.md
tags: [negative-space]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# State type, package and method names, field tags, singleton ids, stored enum values and the OAuth provider are permanent from the first deploy; actors cannot be deleted

**What happened.** Renaming a type or method is a delete plus an add, and the boot is refused. A state id cannot be renamed: a new id is a new empty actor, and the old one is orphaned. User ids are namespaced per provider, so switching providers strands every user's state. Actors cannot be deleted at all, so "delete" is designed as dropping the id from its index.

**Expected.** Treat all of these as permanent from the first deploy.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source.

**Checked at 1.6.0.** `python/references/api-schema-evolution.md` (line ~30 and the table at ~37) says a rename is a delete plus an add; `mcp-ui/references/auth-oauth-providers.md` and `build/SKILL.md` (~292) say switching providers strands user state. Nothing found on renaming a singleton state id, stored enum/stage values, or that actors cannot be deleted (grep `cannot be deleted`, `delete an actor`, `state id`).
