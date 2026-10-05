---
title: `allow()` and `deny()` — Narrow Uses, Not Defaults
impact: HIGH
impactDescription: `allow()` is for genuinely public endpoints; do not use it to silence dev-mode auth warnings or to get tests past `PermissionDenied`
tags: auth, allow, deny, authorizer, rule
summary: "`allow()` only for genuinely public endpoints, never to silence dev warnings, pass tests, or mark \"internal-only\" methods; `deny()` locks a method out; return an instance."
step: auth
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# `allow()` and `deny()` — Narrow Uses, Not Defaults

## When you are here

You are about to return `allow()` / `deny()`, or `allow()` looks like the fix
for a `PermissionDenied` test. Each has one narrow use; neither is a default.
Composing real rules: `auth-allow-if.md`.

## Do this

- Write the real rule **before the tests**: `rbt dev` allows (with a
  warning) calls to a servicer with no `authorizer()`; the `Reboot()` harness
  and production deny them (`servicer-authorizer.md`). Under `oauth=` every
  caller has a verified identity (`dev-{hash}` under `Development()`), so
  `allow_if(...)` works from day one.
- `allow()` only for a deliberately public, anonymous endpoint: health
  check, public catalog read, sign-up.
- `deny()` only to switch a method off without removing it (deprecated
  endpoint).

```python
from reboot.aio.auth.authorizers import allow, deny


class StatusServicer(Status.Servicer):
    def authorizer(self):
        return allow()          # a constructed rule, not `allow`


class LegacyServicer(Legacy.Servicer):
    def authorizer(self):
        return deny()
```

- One method `allow()` / `deny()`, the rest a real rule:
  `<Type>.Authorizer(<method>=allow(), _default=...)` (`servicer-authorizer.md`).
- Everything else gets `allow_if(...)` (`auth-built-in-predicates.md`,
  `auth-custom-predicates.md`).

| Outcome | Meaning |
| --- | --- |
| `Ok` | Allow. `allow()` always returns it. |
| `Unauthenticated` | No valid identity; caller should retry with credentials. |
| `PermissionDenied` | Identity fine but not allowed. `deny()` always returns it. |

## Never

- `return allow` — the function, not a rule. `return allow()`.
- `allow()` on every servicer to silence the `rbt dev` missing-authorizer
  warning — the warning is the TODO list for real rules.
- `allow()` "for now, tighten before shipping" — it survives into production.
- `allow()` because "there's no auth yet" — wire identity:
  `Application(oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(), prod=...)))`
  identifies every caller in dev and prod; an app on `token_verifier=...`
  writes rules once the verifier is wired, no later than the first harness test.
- `allow()` for "methods only called from inside the app" — every Reboot
  method is internet-reachable; use `allow_if(all=[is_app_internal])`.
- `allow()` "to make the example work" in examples, tutorials, or
  scaffolding — the example is what gets copied.
- `allow()` to get tests past `PermissionDenied` — omitting `authorizer()`
  fails too (harness denies). Impersonate:
  `await rbt.create_external_context_as(name, user_id)`; `app_internal=True`
  contexts for internal paths; web apps keep their production
  `token_verifier=...` (`testing-harness.md`, "Test Against the Real
  Authorizers").
- Subclassing each servicer in tests to override `authorizer()` with
  `allow()` — the app's authorization goes untested.
- `deny()` for "only other servicers may call this" — it blocks **every**
  caller, app-internal included. Use `allow_if(all=[is_app_internal])`.

## Limits

- `allow()` / `deny()` ignore `context`, `state`, `request`; decision is fixed.
- One `authorizer()` per servicer, covering every method unless it returns
  `<Type>.Authorizer(...)` with per-method rules.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `aborted with 'PermissionDenied': You are not authorized to call` | Harness: often no `authorizer()`, or a `deny()` | Real `allow_if(...)`; impersonate users in tests |
| `IS MISSING AUTHORIZATION` | `rbt dev` allowed a call to a servicer with no `authorizer()` | Write the rule before the tests |

## See also

- [`servicer-authorizer.md`](servicer-authorizer.md) — when rules are required, per mode
- [`auth-allow-if.md`](auth-allow-if.md) — composing real rules
- [`testing-harness.md`](testing-harness.md) — impersonating users in tests
