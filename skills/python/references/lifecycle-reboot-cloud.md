---
title: Deploy on Reboot Cloud
impact: MEDIUM
impactDescription: Production deployment target — needed when an app graduates beyond `rbt dev run` or a single-machine `rbt serve`.
tags: deploy, cloud, rbt-cloud, scaling, secrets, dockerfile, api-key, docker
summary: "Dev lets through calls Cloud denies (`PermissionDenied`); `rbt cloud up`/`down`, secrets, logs, access; Cloud vs `rbt serve`."
step: deploy
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Deploy on Reboot Cloud

## When you are here

Taking an app from `rbt dev run` to production. Reboot Cloud builds the
Dockerfile, pushes to a managed registry, and runs the app partitioned
across a cluster (horizontal scaling, failover in seconds). Dockerfile:
[`lifecycle-dockerfile.md`](lifecycle-dockerfile.md); secrets:
[`lifecycle-secrets.md`](lifecycle-secrets.md); web frontend and
`allowed_origins`: [`deploy` skill](../../deploy/SKILL.md).

## Do this

### Cloud or `rbt serve`

| Feature | `rbt serve` (EBS) | `rbt serve` (EFS) | Reboot Cloud |
| --- | --- | --- | --- |
| Physical backups | Yes | Yes | Yes |
| Replication | Within availability zone | Within region | Within region |
| HA failover | ~minutes | ~seconds | ~seconds |
| Vertical scaling | Yes | Yes | Yes |
| **Horizontal scaling** | **No** | **No** | **Yes** |

`rbt serve` is one machine you control; Cloud shards state machines
across a cluster, no sharding code needed. Cloud on your own Kubernetes
for strict compliance: ask via Discord or
[`docs.reboot.dev`](https://docs.reboot.dev).

### Access

Sign up at [`cloud.reboot.dev`](https://cloud.reboot.dev/), create an
API key, export it as `REBOOT_CLOUD_API_KEY` (read by every `rbt cloud`
subcommand).

### Deploy: `rbt cloud up`

```sh
export REBOOT_CLOUD_API_KEY=<your-key>
rbt cloud up \
  --application-name=my-app \
  --organization=my-org \
  --size=xsmall
```

- `--application-name`: the app's name in the org; reuse on later
  `cloud` subcommands.
- `--organization`: on **every** `rbt cloud` command, else the app is
  looked up under your user and new apps can't be created. Creating one
  needs a valid payment method on the org.
- `--size`: `xsmall` (default), `small`, `medium`, `large`, `xlarge`.
- `--dockerfile=./Dockerfile` (default); `--docker-build-arg=KEY=VALUE`
  (repeatable) forwards build args.

Success prints three URLs:

```text
  Your API is available at:      https://<application-id>.prod1.rbt.cloud:9991
  MCP clients can connect at:    https://<application-id>.prod1.rbt.cloud:9991/mcp
  You can inspect your state at: https://<application-id>.prod1.rbt.cloud:9991/__/inspect
```

From the terminal, `rbt inspect` against the API URL
([inspect skill](../../inspect/SKILL.md)). To update, `rbt cloud up`
again; it rolls a new revision forward.

### Secrets, logs, teardown

- **Secrets**: `rbt cloud secret set/list/delete`
  ([`lifecycle-secrets.md`](lifecycle-secrets.md)); first `up` before
  first `secret set`.
- **Logs**: `rbt cloud logs`; `--follow` tails, `--revisions=` filters.
- **Teardown**: `rbt cloud down --application-name=... --organization=...
  --expunge` deletes the application's state (see Limits).

### Auth

Every externally reachable method needs an authorizer: without one,
Cloud and `rbt serve` **deny** calls (`PermissionDenied`) while
`rbt dev run` allows them with a 60-second warning, so the gap shows
only on first deploy. See
[`servicer-authorizer.md`](servicer-authorizer.md),
[`auth-allow-if.md`](auth-allow-if.md).

## Never

- **`rbt cloud down` to roll back or pause** — at 1.6.0 it always
  expunges; `--no-expunge` is refused. Roll forward with `rbt cloud up`.
- **`rbt cloud down --expunge` to change size** — resizing is
  non-destructive (Limits).
- **Dropping `--organization` after the first deploy** (Errors).
- **`--api-key=<key>` on the command line** — even `--api-key=$VAR` is
  visible in `ps`; use `REBOOT_CLOUD_API_KEY`.

## Limits

- **`rbt cloud down` always deletes state** at 1.6.0 (source: fails
  without `--expunge`); secrets survive
  ([`lifecycle-secrets.md`](lifecycle-secrets.md)). Only `rbt export` /
  `rbt import` keep data across it or a breaking-change expunge
  ([`lifecycle-backup-restore.md`](lifecycle-backup-restore.md)).
- **Changing `--size` keeps state**: `rbt cloud up` at a new size rolls
  forward like any redeploy (confirmed by Reboot, reboot-crm).
- **`rbt cloud up` returns before the app serves**: `/__/inspect`
  answered 503 for about 30 seconds after `up` exited 0. A 503 carrying
  `access-control-allow-origin` means "still rolling out", not
  "misconfigured" (reboot-crm, 1.6.0).
- **The image push needs `/var/run/docker.sock`**; stock macOS Docker
  Desktop uses `~/.docker/run/docker.sock`, so the push fails though
  `docker` works. Fix in Errors (reboot-crm, 1.6.0).
- **An `oauth=` app needs `allowed_origins`** in production; the default
  is refused at boot. What to list: [`deploy` skill](../../deploy/SKILL.md).

## Scales as

- Horizontal: Cloud partitions actors across machines automatically;
  `rbt serve` scales only vertically (framework design).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `--organization=... is required for new applications` | `cloud up` without `--organization` (new app, or org app looked up under your user) | Add `--organization=<org>` |
| `User '...' does not have an application named '...'. If the application belongs to an organization, try adding --organization=<name>.` | `--organization` left off `down` / `logs` / `secret`; the app exists | Add `--organization=<org>` |
| `Currently all applications brought down are expunged.` | `rbt cloud down --no-expunge` | No non-destructive down; export first to keep data |
| `Organization '...' does not have a valid payment method.` | Creating an app on an org with no payment method | Add one at `cloud.reboot.dev` |
| `push failed: failed to connect to the docker API at unix:///var/run/docker.sock` | macOS Docker Desktop socket is elsewhere | `export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"` |
| `Could not deploy revision` | The new revision failed to start; its logs follow | Fix the cause in the logs and `up` again |
| `` `OAuth` requires `allowed_origins=[...]` to be set explicitly in production `` | `oauth=` with no `allowed_origins` outside `rbt dev run` (the test harness counts as production) | List the SPA's origin, or `allowed_origins=[]` for same-origin only |
| `PermissionDenied` | A method with no authorizer, allowed in dev, denied here | Add an authorizer |

## See also

- [`lifecycle-dockerfile.md`](lifecycle-dockerfile.md) — the image `up` builds
- [`lifecycle-secrets.md`](lifecycle-secrets.md) — Cloud secrets and ordering
- [`../../deploy/SKILL.md`](../../deploy/SKILL.md) — frontend, domain, `allowed_origins`
