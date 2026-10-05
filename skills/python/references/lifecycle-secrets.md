---
title: Set Secrets — Env Vars in Dev, `rbt cloud secret set` in Cloud
impact: HIGH
impactDescription: Wrong delivery mechanism means either committing a secret to git (dev) or seeing `KeyError` at boot (cloud).
tags: secrets, env, environment-variables, rbt-cloud, oauth, api-key, client-secret
summary: "An `--env-file` in dev, `rbt cloud secret set` in Cloud; never in `.rbtrc` or code; a bare `.env` is not auto-loaded; no `REBOOT_*` / `RBT_*` names."
step: shell
applies: [mcp-ui, web-app, backend-only]
always: false
when: "the app needs secrets (API keys, OAuth client secrets)"
verified: 1.6.0
docs: ""
---

# Set Secrets — Env Vars in Dev, `rbt cloud secret set` in Cloud

## When you are here

The app needs an API key, an OAuth client secret or a signing key. The
application always reads a secret the same way, `os.environ["KEY"]`;
what differs is how the value gets into the environment. The `.rbtrc`
flag itself is in [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md); deploying
is [`lifecycle-reboot-cloud.md`](lifecycle-reboot-cloud.md).

## Do this

| Where the app runs | Mechanism | Where the value lives |
| --- | --- | --- |
| `rbt dev run` | `--env-file=<path>` named in `.rbtrc`; or `--env=KEY=VALUE`; or an exported shell variable | A git-ignored `.env` / launch flags / the shell |
| Reboot Cloud | `rbt cloud secret set KEY` (reads the value from the operator's shell) | The application's secret store |

The two never share storage: a Cloud secret does not reach local
`rbt dev run`, and an exported shell variable does not reach Cloud.

### In dev: one `.env`, named once in `.rbtrc`

```sh
# .env — at the project root, listed in .gitignore
STRIPE_API_KEY=sk_test_...
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
```

```sh
# .rbtrc
dev run --env-file=.env
```

Every `rbt dev run` sets those variables before launching the app, and
editing the file while it runs restarts the app. Standard `.env`
syntax: `KEY=VALUE`, `#` comments, blank lines, optional `export `,
quoted values. For a one-off value, `--env=KEY=VALUE` (repeatable)
overrides the file; variables exported in the launching shell are
inherited too:

```sh
uv run rbt dev run --env=FEATURE_FLAG=on
```

### In Cloud: `rbt cloud secret set`, all keys in one call

```sh
# Values come from your shell env, so they stay out of shell history
# and process listings. The API key is read from REBOOT_CLOUD_API_KEY.
export REBOOT_CLOUD_API_KEY=<your-key>
export AUTH0_DOMAIN=... AUTH0_CLIENT_ID=... AUTH0_CLIENT_SECRET=...
rbt cloud secret set \
  AUTH0_DOMAIN AUTH0_CLIENT_ID AUTH0_CLIENT_SECRET \
  --application-name=my-app \
  --organization=my-org

# KEY=VALUE inline puts the value in shell history; non-sensitive only.
rbt cloud secret set FEATURE_FLAG=on ...

# Same --application-name / --organization as `set`.
rbt cloud secret list ...
rbt cloud secret delete AUTH0_CLIENT_SECRET ...
```

When the app is up, the Cloud backend rolls out a new revision on its
own after `secret set`, with the values in `os.environ`. One call with
every key rolls out once; one call per key rolls out once per call.
Secrets are application-scoped.

### Reading secrets in application code

```python
import os

# Fail fast at startup if a required secret is missing:
STRIPE_API_KEY = os.environ["STRIPE_API_KEY"]

# Optional secrets with a sensible default:
DEBUG_MODE = os.environ.get("DEBUG_MODE", "off")
```

`Application(oauth=...)` takes provider credentials as plain strings:

```python
from reboot.aio.auth.oauth import OAuth
from reboot.aio.auth.oauth_providers import Google

async def main():
    await Application(
        servicers=[UserServicer, CounterServicer],
        oauth=OAuth(
            provider=Google(
                client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
                client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
            ),
        ),
    ).run()
```

`auth-oauth-providers.md` (`mcp-ui` skill) covers swapping providers.

## Never

- **A secret in `main.py`, servicer code or any source file** —
  anything checked into git is leaked.
- **A `--env=KEY=secret` line in `.rbtrc`** — `.rbtrc` is checked in.
  `dev run --env-file=.env` is fine; it is only a path.
- **Relying on a bare `.env` being auto-loaded** — Reboot reads it
  only when `rbt dev run` gets `--env-file=.env` (in `.rbtrc` or on
  the command line).
- **`rbt cloud up` after `rbt cloud secret set`** — the backend
  already rolled out a new revision; a second `up` is a redundant
  rollout.
- **One `rbt cloud secret set` per key** — each call rolls the app
  out again. Pass every key to one call.
- **A `REBOOT_*` or `RBT_*` name** — reserved by the platform;
  `secret set` refuses it.
- **Assuming dev and Cloud share secrets** — configure each with its
  own mechanism.

## Limits

- **`rbt cloud secret set` needs the application to exist.** Before
  the first `rbt cloud up` it fails with "does not have an application
  named". So `up` comes first, and an app that cannot boot without its
  secrets (a `prod=Google(...)` provider reading
  `os.environ[...]`) cannot start in its first revision; it becomes
  healthy once `secret set` rolls out the next one. Expect that on
  creation only (reboot-crm, 1.6.0).
- **Secrets outlive the app's state.** `rbt cloud down --expunge`
  deletes state but keeps the secrets, and `rbt cloud secret list`
  answers while the app is down; the next `cloud up` boots with them
  (reboot-crm, 1.6.0).
- **Names** are uppercase environment identifiers: letters, digits,
  underscores, not starting with a digit (`rbt cloud secret set
  --help`, 1.6.0).
- **`--env-file` is `dev run` only** — not `rbt serve`, not Cloud. A
  self-hosted `rbt serve` takes secrets from its own environment.

## Scales as

- Each `rbt cloud secret set` call is one rollout of the app.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Organization '...' does not have an application named '...'` | `secret set` before the first `rbt cloud up`, or a misspelled name | `rbt cloud up` first, then `secret set` |
| `User '...' does not have an application named '...'. If the application belongs to an organization, try adding --organization=<name>.` | `--organization` was left off; the app is looked up under your user | Add `--organization=<org>` |
| `'KEY' environment variable not found: please set this environment variable or pass 'KEY=[VALUE]` | A bare `KEY` argument with nothing exported in the shell | `export KEY=...` first |
| `KeyError: 'STRIPE_API_KEY'` (at app boot) | The secret is not set in this environment | `.env` + `--env-file` in dev; `rbt cloud secret set` in Cloud |

## See also

- [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md) — the `--env-file` line
- [`lifecycle-reboot-cloud.md`](lifecycle-reboot-cloud.md) — deploy order and flags
- [`../../deploy/SKILL.md`](../../deploy/SKILL.md) — full production deploy
