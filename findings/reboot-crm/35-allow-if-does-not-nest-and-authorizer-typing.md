---
id: reboot-crm-35
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.2"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/auth-custom-predicates.md
  - python/references/auth-allow-if.md
tags: [contradiction, auth, negative-space]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/auth-allow-if.md § Never; python/references/auth-custom-predicates.md § Never"
---

# allow_if does not nest, and the generated authorizer wants a differently-typed rule than the reference describes

**What happened.** Found through `mypy`. (1) `allow_if(any=[is_app_internal, allow_if(all=[is_teammate, is_owner])])` does not type-check: an `AuthorizerRule` is not an `AuthorizerCallable`, so a rule cannot be a member of another rule; the composition has to be flattened into one predicate. (2) `auth-custom-predicates.md` says a predicate's `state` should be the pydantic `<X>State`, not `<Type>Authorizer.StateType` (protobuf), but the generated `Chat.Authorizer(_default=...)` wants an `AuthorizerRule[Chat, Message]` (the protobuf pair), so a helper returning `AuthorizerRule[ChatState, Any]` is rejected at the point of use. The working shape is a predicate annotated with the pydantic state and a helper returning `AuthorizerRule[Any, Any]`, which the framework's own `auth.py` helpers already do.

**Expected.** A sentence saying rules do not compose (combine in one predicate) and an example of a helper return type the generated authorizer accepts. Fixes proposed: let rules compose; reconcile the typing in `auth-custom-predicates.md`. Recommendation: the documentation fix first and urgently.

**Repro.** Not recorded.

**Where in the skills.** `python/references/auth-custom-predicates.md` (state annotation note ~line 77, helper example ~line 112 returning `AuthorizerRule[TaskListState, Any]`), `python/references/auth-allow-if.md`.

**Checked at 1.6.0.** `auth-custom-predicates.md` line ~77 still says not to use `Authorizer.StateType`, and line ~112 still shows `AuthorizerRule[TaskListState, Any]`; no text says rules do not nest.
