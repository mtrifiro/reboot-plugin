---
id: crm-kit-28
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §4"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/auth-allow-if.md
  - python/references/auth-custom-predicates.md
tags: [auth]
cluster: "4.1"
duplicate_of: reboot-crm-35
still_applies: no
status: Resolved
resolved_by: "python/references/auth-allow-if.md § Never; python/references/auth-custom-predicates.md § Never"
---

# Never nest allow_if; type rule helpers as AuthorizerRule[Any, Any]

**What happened.** A nested `allow_if` does not type-check: write one predicate that asks both questions, annotate its `state` as the pydantic `<X>State`. A helper typed `AuthorizerRule[<X>State, Any]` is rejected by the generated `Authorizer(...)`, which wants the protobuf pair. §11: `auth-custom-predicates.md`'s `AuthorizerRule[TaskListState, Any]` helper is rejected.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `auth-custom-predicates.md` (§11).

**Checked at 1.6.0.** `auth-custom-predicates.md` § Never now says rules don't nest and to return `AuthorizerRule[Any, Any]`.
