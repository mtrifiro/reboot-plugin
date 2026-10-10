---
id: restaurant-app-3-07
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Plugin skills, item 4"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/auth-custom-predicates.md
  - python/references/auth-allow-if.md
tags: [auth, error-text]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# The custom-predicate example's `state: XState | None` fails mypy inside `allow_if`

**What happened.** A predicate written like the reference's `is_owner` (`state: TaskListState | None = None`, line ~46), used as `allow_if(all=[is_checks_server_or_manager])`, failed `uv run mypy backend/` with `error: Value of type variable "ContravariantStateType" of "allow_if" cannot be "CheckState | None"  [type-var]`. Annotating `state: Any = None` and narrowing with `isinstance(state, CheckState)` passed. Seen once; it may depend on the predicate being async. reboot-crm's P3.2 (reboot-crm-35) found a different typing mismatch in the same reference, since marked Resolved.

**Expected.** Either the example type-checks as written, or the reference shows the `Any` + `isinstance` form; or the generated `Authorizer` typing needs a fix. Worth reproducing against the reference's own `TaskList` example.

**Repro.** The reference's `is_owner` against a generated `<Type>.Authorizer(method=allow_if(all=[is_owner]))`, then `uv run mypy backend/`.

**Where in the skills.** `python/references/auth-custom-predicates.md`, Do this; `python/references/auth-allow-if.md`.
