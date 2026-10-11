---
title: Back Up and Restore — `rbt export`, Expunge, `rbt import`
impact: HIGH
impactDescription: Every breaking API change costs an expunge, and an expunge deletes every user's data unless it was exported first and imported after
tags: deploy, backup, restore, export, import, expunge, migration, breaking-change, cloud
summary: "Every deploy backs up first; a breaking change is back up, expunge, boot, restore, boot, compare."
step: deploy
applies: [mcp-ui, web-app, backend-only]
always: false
when: "an app in production needs an expunge (an API removal), or its data needs backing up or restoring"
verified: 1.6.0
docs: ""
---

# Back Up and Restore — `rbt export`, Expunge, `rbt import`

## When you are here

An app holds data someone would miss, and either a deploy is about to
run (every one backs up first), or the API lost or renamed something,
so `scripts/deploy.sh` refused ("needs an expunge and a restore") and
the old state has to go and come back. `rbt export` and `rbt import`
are the only sound backup: `rbt cloud down` always expunges, and a
rejected deploy is not recoverable any other way
([`api-schema-evolution.md`](api-schema-evolution.md)).

The build templates ship the scripts; copy them in from
`build/templates/<front-door>/` if the project predates them:

| File | What it does |
| --- | --- |
| `scripts/backup.sh dev\|prod` | `rbt export` to `exports/backups/<env>-<stamp>/data/`, a `manifest.json` (commit, rbt version, actors per type); refuses an empty export |
| `deploy/before-backend` | Run by `scripts/deploy.sh` before every `rbt cloud up`: `backup.sh prod`, so a failed backup stops the deploy. Skips only the first deploy |
| `scripts/restore.py dev\|prod <backup>` | Dry run by default: leaves out what the boot rebuilds, checks every line against this checkout's API, refuses an application that is not empty; `--apply` runs `rbt import` |
| `scripts/compare_exports.py <before> <after>` | Every actor the backup had is there; exit 1 on a missing one |
| `scripts/migrations/rules.py` | Rules a migration composes: `drop_field`, `rename_field`, `drop_type`, `drop_tasks`, `move_types`, `drop_records`, `compose` |
| `tests/backup_restore_test.py` | The round trip against the harness's real export and import services |

`exports/` is git-ignored: a backup is every user's data.

## Do this

### Every deploy

Nothing to do: `deploy/before-backend` runs `scripts/backup.sh prod`,
which reads the API address from `deploy/ledger.jsonl` (`api_url`, which
`scripts/deploy.sh` records) and the key from `.deploy.env`
(`REBOOT_CLOUD_API_KEY`, which `rbt export` accepts as the admin
credential on `*.rbt.cloud`). Read the counts it prints. An app already
in production when the scripts arrive needs both fields in the ledger,
or the backup, and so the deploy, stops:

```sh
echo '{"backend_commit": "<sha it runs>", "api_url": "https://<id>.<cell>.rbt.cloud"}' >> deploy/ledger.jsonl
```

By hand, run `scripts/backup.sh prod` **on its own**: never chained
with `;` (the next command runs whether it worked or not) or a pipe
(which hides its exit status).

### Set the project's restore rules

At the top of `scripts/restore.py`, once:

- `MUST_BE_EMPTY` — `None` checks every type of the app's own servicers.
  If `initialize` creates actors on every boot, list only the types a
  fresh boot leaves empty.
- `BOOT_TASKS` — every `(state type, Method)` the boot starts (a loop
  `initialize` begins). The import restarts every incomplete task, so
  one left in would run beside the boot's own; the restore leaves it,
  its idempotency records and its pending queue `dequeue` out.
- `initialize`'s aliases name what they act on (`"loop on <queue id>"`),
  not the boot: the backup's idempotency records come back under the
  same keys ([`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md)).

### A breaking change: back up, expunge, boot, restore, boot, compare

```sh
set -a; . ./.deploy.env; . deploy/config; set +a
ORG="--organization=$REBOOT_CLOUD_ORGANIZATION"

# 0. On the release branch. A removed or renamed state field, a type
#    that moved package, or a stored value whose meaning changed needs
#    a migration: scripts/migrations/<name>.py (rules.py's docstring
#    has the shape). Renumbered tags and a new --size need none.

# 1. Back up, with nobody working: the export is not a snapshot.
scripts/backup.sh prod                    # -> exports/backups/prod-<stamp>/

# 2. Rehearse on the dev loop, on the new code:
#    rbt dev expunge --yes; rbt dev run; then
uv run python scripts/restore.py dev exports/backups/prod-<stamp> --rehearsal [--migration <name>]
#    again with --apply, restart rbt dev run, and look at the app.

# 3. Down, expunging. 4. Up on the new code, with deploy.sh's flags.
uv run rbt cloud down --application-name="$APP" $ORG --expunge
uv run rbt cloud up --application-name="$APP" --size="$SIZE" $ORG

# 5. Wait until every replica answers: /__/inspect returns 200 on the
#    first one, and import fans out to all of them.
until uv run rbt inspect state list --type=<a type> --application-url=<api_url> >/dev/null 2>&1; do sleep 15; done

# 6. Restore: dry run, then --apply. A failed --apply can run again.
uv run python scripts/restore.py prod exports/backups/prod-<stamp> [--migration <name>]
uv run python scripts/restore.py prod exports/backups/prod-<stamp> [--migration <name>] --apply

# 7. Boot again, so `initialize` runs over the restored data.
uv run rbt cloud up --application-name="$APP" --size="$SIZE" $ORG

# 8. Record the new code as what production runs: the next deploy's
#    API check compares against it. Commit and push.
echo '{"backend_commit": "<sha>", "api_url": "<the address up printed>"}' >> deploy/ledger.jsonl

# 9. Publish the frontend: the old bundle still calls what the backend
#    dropped.
scripts/deploy.sh --frontend-only

# 10. Prove it.
scripts/backup.sh prod
uv run python scripts/compare_exports.py exports/backups/prod-<stamp> exports/backups/prod-<new> [--migration <name>]
```

`compare_exports.py` passes when nothing is missing; changed fields
should be only what the boot recomputes and work that finished since.

## Never

- Never expunge without a backup taken after the last write, checked
  by its counts.
- Never `rbt import` into an application holding data: it overwrites
  what the backup has and deletes nothing, so the result is a merge
  of two states. Roll back on a live app by expunging first.
- Never put a dev backup into production: its users are the
  Development picker's identities. `restore.py` refuses it, and asks
  for `--rehearsal` the other way round.
- Never edit a backup in place; a migration rewrites the lines on the
  way in and leaves the backup as it was taken.
- Never commit `exports/`.

## Limits

- **Not a point-in-time snapshot.** Servers export concurrently, type
  by type, with writers running.
- **By field name.** Import parses each state against the running
  application's types and refuses an unknown name, stopping part-way
  with only "Failed to parse import item, is it possible the types
  being imported are not backwards compatible?"; what it wrote stays.
  `restore.py` runs the same parse locally first.
- **Tasks restart.** Every incomplete task in the backup is dispatched
  again after the import (`BOOT_TASKS` above).
- **Idempotency keys survive an expunge** (seeded from the
  application's id, which survives too, with its secrets), so the
  backup's records replace those the fresh boot wrote.
- **An emptied stdlib `SortedMap` comes back unreadable** ("Failed to
  find column family ... SortedMapEntry"): the import constructs
  nothing. `restore.py` leaves such maps out and the `Queue` that
  used one makes a new one.
- **Types and ids travel; tags do not matter.** A package move changes
  every `state_ref` (its prefix hashes the full type name):
  `move_types` rewrites them. A different `--size` needs nothing.
- **Encrypted values stay with their deployment.** The stdlib
  ciphertext and OAuth token stores encrypt under the deployment's
  root keys: a restore into the same application after an expunge
  reads them, one into another application cannot, and users connect
  again.
- **`rbt export --config=<name>` does not expand an
  `export:<name> --application-url=` `.rbtrc` line** (1.6.0); the
  scripts pass the address themselves.

## Scales as

Export and import stream JSON lines, one file per server; time grows
with actor count (reboot-crm's production backup: ~9,600 lines).
`restore.py` holds the whole backup in memory to pair lines across
files, fine to hundreds of thousands of lines.

## Errors you will see

| Error / symptom | Meaning | Fix |
| --- | --- | --- |
| `backup: ... the export holds nothing; this is not a backup` | Export succeeded with no lines: wrong address, or an app that was expunged | Check `api_url` in `deploy/ledger.jsonl`; do not deploy |
| `deploy/ledger.jsonl records no api_url` | An app already in production, ledger seeded without its address | Append the `api_url` line above |
| `refused: the application is not empty` | `rbt import` would merge | Expunge first, or narrow `MUST_BE_EMPTY` if the boot creates those actors |
| `no such state type in this checkout` / `... a type this checkout moved` | The backup predates a type removal or package move | A migration (`drop_type`, `move_types`); add the prefix to `RETIRED_PACKAGES` |
| `(state): Message type "..." has no field named "..."` | A removed or renamed field | `drop_field` / `rename_field` migration |
| `refused: the application did not answer rbt inspect state list` | Cloud replicas still starting | Wait a minute and run again |
| `Failed to find column family for state type 'rbt.std.collections.v1.SortedMapEntry'` | An emptied `SortedMap` imported without `restore.py` | Restore through `restore.py` |

## See also

- [`api-schema-evolution.md`](api-schema-evolution.md) — which API changes need this
- [`lifecycle-reboot-cloud.md`](lifecycle-reboot-cloud.md) — `rbt cloud up`/`down`, secrets
- [`deploy` skill](../../deploy/SKILL.md) — `scripts/deploy.sh` and the ledger
