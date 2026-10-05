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

The app needs an API key, OAuth client secret or signing key. Code
always reads `os.environ["KEY"]`; only delivery into the environment
differs. The `.rbtrc` flag: [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md);
deploying: [`lifecycle-reboot-cloud.md`](lifecycle-reboot-cloud.md).

## Do this

- `rbt dev run`: a git-ignored `.env` named by `--env-file=<path>` in
  `.rbtrc`, `--env=KEY=VALUE`, or an exported shell variable.
- Reboot Cloud: `rbt cloud secret set KEY` (value read from the
  operator's shell) into the application's secret store.
- They never share storage: neither reaches the other.

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

`rbt dev run` sets these before launch; editing the file restarts the
app. Syntax: `KEY=VALUE`, `#` comments, blank lines, optional `export `,
quoted values. `--env=KEY=VALUE` (repeatable) overrides the file;
variables exported in the launching shell are inherited:

```sh
uv run rbt dev run --env=FEATURE_FLAG=on
```

### In Cloud: `rbt cloud secret set`, all keys in one call

```sh
# Values come from your shell env: out of history and process listings.
export REBOOT_CLOUD_API_KEY=<your-key>
export AUTH0_DOMAIN=... AUTH0_CLIENT_ID=... AUTH0_CLIENT_SECRET=...
rbt cloud secret set \
  AUTH0_DOMAIN AUTH0_CLIENT_ID AUTH0_CLIENT_SECRET \
  --application-name=my-app \
  --organization=my-org

# KEY=VALUE inline lands in shell history; non-sensitive only.
rbt cloud secret set FEATURE_FLAG=on ...

# Same --application-name / --organization as `set`.
rbt cloud secret list ...
rbt cloud secret delete AUTH0_CLIENT_SECRET ...
```

On a running app, `secret set` rolls out a new revision by itself with
the values in `os.environ` — once per call, so pass every key in one
call. Secrets are application-scoped.

### Reading secrets in application code

```python
import os

STRIPE_API_KEY = os.environ["STRIPE_API_KEY"]       # required: fail fast at startup
DEBUG_MODE = os.environ.get("DEBUG_MODE", "off")    # optional, with default
```

`Application(oauth=...)` takes provider credentials as plain strings
(swapping providers: `auth-oauth-providers.md`, `mcp-ui` skill):

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

## Never

- **A secret in `main.py`, servicer code or any source file** — anything
  in git is leaked.
- **A `--env=KEY=secret` line in `.rbtrc`** — it's checked in.
  `dev run --env-file=.env` is fine; it's only a path.
- **Relying on a bare `.env` being auto-loaded** — read only when
  `rbt dev run` gets `--env-file=.env` (`.rbtrc` or command line).
- **`rbt cloud up` after `rbt cloud secret set`**, or one `secret set`
  per key — each is a redundant rollout.
- **A `REBOOT_*` or `RBT_*` name** — reserved; `secret set` refuses it.

## Limits

- **`rbt cloud secret set` needs the application to exist**; before the
  first `rbt cloud up` it fails with "does not have an application
  named". So `up` comes first, and an app that can't boot without its
  secrets (a `prod=Google(...)` provider reading `os.environ[...]`)
  fails its first revision, becoming healthy once `secret set` rolls out
  the next. Expect that on creation only (reboot-crm, 1.6.0).
- **Secrets outlive state**: `rbt cloud down --expunge` keeps them,
  `rbt cloud secret list` answers while the app is down, and the next
  `cloud up` boots with them (reboot-crm, 1.6.0).
- **Names**: uppercase env identifiers — letters, digits, underscores,
  not starting with a digit (`rbt cloud secret set --help`, 1.6.0).
- **`--env-file` is `dev run` only** — not `rbt serve`, not Cloud; a
  self-hosted `rbt serve` takes secrets from its own environment.

## Scales as

- Each `rbt cloud secret set` call is one rollout of the app.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Organization '...' does not have an application named '...'` | `secret set` before the first `rbt cloud up`, or a misspelled name | `rbt cloud up` first, then `secret set` |
| `User '...' does not have an application named '...'. If the application belongs to an organization, try adding --organization=<name>.` | `--organization` left off; app looked up under your user | Add `--organization=<org>` |
| `'KEY' environment variable not found: please set this environment variable or pass 'KEY=[VALUE]` | Bare `KEY` argument, nothing exported | `export KEY=...` first |
| `KeyError: 'STRIPE_API_KEY'` (at app boot) | Secret not set in this environment | `.env` + `--env-file` in dev; `rbt cloud secret set` in Cloud |

## See also

- [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md) — the `--env-file` line
- [`lifecycle-reboot-cloud.md`](lifecycle-reboot-cloud.md) — deploy order and flags
- [`../../deploy/SKILL.md`](../../deploy/SKILL.md) — full production deploy
