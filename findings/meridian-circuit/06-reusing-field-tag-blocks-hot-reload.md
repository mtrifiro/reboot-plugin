---
id: meridian-circuit-06
project: meridian-circuit
source: "v 1.4.1 Reboot/meridian-circuit/docs/2026.08.18 reboot-learnings porting supabase app.md §6"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/api-schema-evolution.md
  - python/references/lifecycle-dev-loop.md
tags: [error-text, operations]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "python/references/api-schema-evolution.md § Errors you will see"
---

# Reusing a field tag for a new field blocks the hot reload

**What happened.** Removing `pulse: int = Field(tag=2)` and adding `showing_stats: list[ShowingStats] = Field(tag=2)` stops `rbt dev run` dead: ``- Field `showing_stats` in the state of servicer type `circuit.v1.circuit.Chain` has switched type from `double` to `message` `` / `Backwards incompatibility encountered ... waiting for modification`. Tags are permanent. Either keep the old field as a deprecated default and number the new one fresh, or (pre-release, only seed data at stake) `uv run rbt dev expunge --yes` and restart.

**Expected.** Not recorded.

**Repro.** Replace a field with a differently typed one under the same tag while `rbt dev run` watches.

**Where in the skills.** `python/references/api-schema-evolution.md`, `lifecycle-dev-loop.md`.

**Checked at 1.6.0.** `api-schema-evolution.md` § Errors you will see maps `has switched type from` to 'A field's type changed: New field, new `tag`'; `lifecycle-dev-loop.md` § Errors you will see adds the expunge route.
