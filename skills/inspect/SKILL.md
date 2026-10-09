---
name: inspect
description: Inspect the live state of a running Reboot application from the command line with `rbt inspect` — list its state types, list the state IDs (actor IDs) of a type, print one actor's state as JSON. Works against a local `rbt dev run` backend and a deployed Reboot Cloud app via `--application-url` and `--admin-credential`. Use to answer "what state types does this app have?", "which actors of this type exist?", "what is stored in this actor right now?" — debugging persisted state from the terminal instead of the `/__/inspect` web dashboard.
argument-hint: "[type list | state list --type=<full.Name> | state get --type=<full.Name> --id=<id>]"
allowed-tools: Bash, Read
---

# inspect — Inspect a Running Reboot Application's State

> **Version notices:** if `rbt` reports a version mismatch or a newer
> Reboot, follow the [upgrade skill](../upgrade/SKILL.md).

`rbt inspect` reads (never modifies) the persisted state of a
**running** app — what the `/__/inspect` web dashboard shows, but
scriptable. Use it for _runtime state_ questions ("did `create` persist
this field?", "which account IDs exist?", "what does actor `alice` hold
now?"). To start an app first see the [run skill](../run/SKILL.md); to
change what it stores, the [`build` skill](../build/SKILL.md)'s Update
Flow (backend-only: the [python skill](../python/SKILL.md)).

## The three operations

Drill down: `type list` for the exact `--type`, `state list` for the
`--id`, `state get` to dump the actor.

```sh
# 1. List the application's registered state types (full names).
rbt inspect type list --application-url=<url>

# 2. List the known state IDs (actor IDs) for one type.
rbt inspect state list --type=<full.Type.Name> --application-url=<url>

# 3. Print a single actor's state as JSON.
rbt inspect state get --type=<full.Type.Name> --id=<state-id> \
  --application-url=<url>
```

- `--type`: the **full, package-qualified** name as `type list` prints
  it (e.g. `bank.v1.Account`, `tests.reboot.Echo`), not the Python class
  name.
- `--id`: the state ID passed to `<Type>.ref(id)` /
  `<Type>.create(context, id, ...)`.

## Connecting: `--application-url` and `--admin-credential`

Both match `rbt export` / `rbt import` (see
`../python/references/lifecycle-reboot-cloud.md`).

- `--application-url` is **required on every command**, local dev
  included — no default from `.rbtrc` or the dev port (1.6.0 `--help`).
  It's the API URL printed as **"Your API is available at:"**, **not**
  the `/__/inspect` page:
  - **Local dev:** what `rbt dev run` prints (e.g.
    `http://localhost:9991`).
  - **Reboot Cloud:** what `rbt cloud up` prints (e.g.
    `https://<application-id>.prod1.rbt.cloud:9991`).
- `--admin-credential`: the app's admin secret
  (`SECRET_REBOOT_ADMIN_TOKEN`).
  - **Local dev:** defaults to `dev`; omit it.
  - **Reboot Cloud:** required — the value set for
    `SECRET_REBOOT_ADMIN_TOKEN` (see
    `../python/references/lifecycle-secrets.md`), or the
    `REBOOT_ADMIN_CREDENTIAL` env var. A `*.rbt.cloud` URL also accepts
    `--api-key` (or `REBOOT_CLOUD_API_KEY`), the Reboot Cloud API key,
    instead (1.6.0 `--help`).

```sh
# Local (admin credential defaults to dev)
rbt inspect state list \
  --type=bank.v1.Account \
  --application-url=http://localhost:9991

# Reboot Cloud (admin credential required)
rbt inspect state get \
  --type=bank.v1.Account --id=alice \
  --application-url=https://<application-id>.prod1.rbt.cloud:9991 \
  --admin-credential="$SECRET_REBOOT_ADMIN_TOKEN"
```

## Notes

- **Read-only**: safe against production.
- **`state get` routes to the actor's host automatically**, even
  multi-server, and reassembles large states transparently.
- **Pipeable**: `type list` / `state list` print one entry per line,
  `state get` one JSON object; no color off a TTY, so `grep` and `jq`
  compose.
- **Web equivalent**: the `/__/inspect` page (linked from `rbt dev run`
  and `rbt cloud up` output) also shows recent calls.

## Known issues

| Error / symptom | Meaning | Fix |
| --- | --- | --- |
| `error: the following arguments are required: --application-url` | Every command needs it, even local dev | `--application-url=http://localhost:<port>` (as `rbt dev run` prints) |
| `expected --type=VALUE, missing '=VALUE'` | `--type` (and the other flags) take only the `=` form | Write `--type=<full.Type.Name>` |
| `Unknown state reference`, or an actor you seeded is missing | Wrong application (port or `--application-name`), or orphans from an earlier `rbt dev run` hold another generation of state (1.4.1) | Check the URL; stop every process per the [run skill](../run/SKILL.md) § "Stop, restart, reset" and start once |
| A repeated field prints as `{"items": [...]}` in one place and as a plain array in another | Inconsistent output shape for lists (reboot-crm, 1.6.0) | Handle both shapes in scripts (`jq 'if type == "object" then .items else . end'`) |
| An `OrderedMap` shows only an id | The map actor holds a root id; its keys and values live in a `Node` actor (client-portal, 1.6.0) | Run `state get` again on the node id |
| A call hangs with `Timed out waiting 30.0s to acquire exclusive lock` | Something holds the actor's lock; `rbt inspect` can't show locks (only `type list`, `state list`, `state get`; 1.6.0) | See [`../python/references/servicer-transaction.md`](../python/references/servicer-transaction.md); a caller that vanished mid-transaction keeps the lock until the app restarts |
