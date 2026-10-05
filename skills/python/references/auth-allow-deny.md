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

You are about to return `allow()` or `deny()` from an `authorizer()`,
or a test just failed with `PermissionDenied` and `allow()` looks like
the quick fix. Both are valid rule instances with one narrow use each;
neither is a default. When to write rules at all is
`servicer-authorizer.md`; composing real rules is `auth-allow-if.md`.

## Do this

Write the real rule **before the tests**. `rbt dev` allows calls on a
servicer with no `authorizer()` (with a warning), but the `Reboot()`
test harness denies them with `PermissionDenied`, as production does
(`servicer-authorizer.md`). Under `oauth=` every caller already has a
verified identity (`dev-{hash}` under `Development()`), so a real
`allow_if(...)` rule works from day one.

Use `allow()` only for an endpoint you have consciously decided is
public — any caller on the internet, anonymously: a health check, an
unauthenticated catalog read, a public sign-up. Open access is the
product, not an accident.

Use `deny()` only to switch a method off without removing it from the
API (e.g. a deprecated endpoint not yet deleted):

```python
from reboot.aio.auth.authorizers import allow, deny


class StatusServicer(Status.Servicer):
    def authorizer(self):
        return allow()          # a constructed rule, not `allow`


class LegacyServicer(Legacy.Servicer):
    def authorizer(self):
        return deny()
```

To give one method of a type `allow()` / `deny()` and the rest a real
rule, use `<Type>.Authorizer(<method>=allow(), _default=...)`
(`servicer-authorizer.md`).

A rule's decision is one of:

| Outcome | Meaning |
| --- | --- |
| `Ok` | Allow the call. `allow()` always returns it. |
| `Unauthenticated` | No valid identity attached; the caller should retry with credentials. |
| `PermissionDenied` | Identity is fine but not allowed. `deny()` always returns it. |

Everything reachable from a browser, an MCP client, an external
service, or any caller you'd want to identify gets an `allow_if(...)`
rule built from `auth-built-in-predicates.md` / `auth-custom-predicates.md`.

## Never

- `return allow` — the function, not a rule. `return allow()`.
- `allow()` on every servicer to silence the `rbt dev` missing-authorizer
  warning — the warning is the TODO list for real rules.
- `allow()` "for now, tighten before shipping" — you lose track of which
  servicers needed real rules, and the `allow()` survives into production.
- `allow()` because "there's no auth yet" — wire identity instead:
  `Application(oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(), prod=...)))`
  gives every caller a real identity in dev and prod; an app on
  `token_verifier=...` writes its rules once the verifier is wired, and
  no later than the first harness test.
- `allow()` for "methods only called from inside the app" — every Reboot
  method is reachable from the internet; no network boundary makes one
  app-internal. Say so: `allow_if(all=[is_app_internal])`.
- `allow()` "to make the example work" in examples, tutorials, or
  scaffolding — write the real rule; the example is what gets copied.
- `allow()` to get tests past `PermissionDenied` — omitting
  `authorizer()` doesn't work either (the harness denies). Impersonate:
  `await rbt.create_external_context_as(name, user_id)`; use
  `app_internal=True` contexts for internal paths. Web apps keep their
  production `token_verifier=...`: the harness's OAuth server verifies
  the token `create_external_context_as` mints, and a hand-built bearer
  still hits the app's verifier (`testing-harness.md`, "Test Against the
  Real Authorizers", including its last-resort carve-out).
- Subclassing each servicer in tests to override `authorizer()` with
  `allow()` — the app's authorization goes untested.
- `deny()` for "only other servicers may call this" — `deny()` blocks
  **every** caller, app-internal ones included. Use
  `allow_if(all=[is_app_internal])`.

## Limits

- `allow()` and `deny()` ignore `context`, `state`, and `request`; their
  decision is fixed.
- One `authorizer()` per servicer; it covers every method unless it
  returns `<Type>.Authorizer(...)` with per-method rules.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `aborted with 'PermissionDenied': You are not authorized to call` | In the test harness, often a servicer with no `authorizer()`, or a `deny()` | Write the real `allow_if(...)` rule; impersonate users in tests, not `allow()` |
| `IS MISSING AUTHORIZATION` | `rbt dev` allowed a call to a servicer with no `authorizer()` | Write the rule before the tests |

## See also

- [`servicer-authorizer.md`](servicer-authorizer.md) — when rules are required, per mode
- [`auth-allow-if.md`](auth-allow-if.md) — composing real rules
- [`testing-harness.md`](testing-harness.md) — impersonating users in tests
