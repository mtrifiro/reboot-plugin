---
title: Deploy on Reboot Cloud
impact: MEDIUM
impactDescription: Production deployment target — needed when an app graduates beyond `rbt dev run` or a single-machine `rbt serve`.
tags: deploy, cloud, rbt-cloud, scaling, secrets, dockerfile, api-key, docker
summary: "`rbt cloud up` / `down`, secrets, logs and getting access; when Cloud beats `rbt serve`; calls the dev server let through are `PermissionDenied` on Cloud."
step: deploy
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Deploy on Reboot Cloud

## When you are here

The app works under `rbt dev run` and is going to production. Reboot
Cloud takes the project's Dockerfile, builds and pushes the image to a
managed registry, and runs the app partitioned across a cluster, with
horizontal scaling and failover in seconds. The Dockerfile is
[`lifecycle-dockerfile.md`](lifecycle-dockerfile.md); secrets are
[`lifecycle-secrets.md`](lifecycle-secrets.md); publishing a web
frontend and `allowed_origins` are the
[`deploy` skill](../../deploy/SKILL.md).

## Do this

### Cloud or `rbt serve`

| Feature | `rbt serve` (EBS) | `rbt serve` (EFS) | Reboot Cloud |
| --- | --- | --- | --- |
| Physical backups | Yes | Yes | Yes |
| Replication | Within availability zone | Within region | Within region |
| HA failover | ~minutes | ~seconds | ~seconds |
| Vertical scaling | Yes | Yes | Yes |
| **Horizontal scaling** | **No** | **No** | **Yes** |

`rbt serve` runs on one machine you control. Cloud shards the app's
state machines across a cluster with no sharding logic in user code.
Enterprises with strict compliance needs can run Cloud on their own
Kubernetes cluster (ask via the Discord community or
[`docs.reboot.dev`](https://docs.reboot.dev)).

### Access

Sign up at [`cloud.reboot.dev`](https://cloud.reboot.dev/), create an
API key, and export it as `REBOOT_CLOUD_API_KEY`. Every `rbt cloud`
subcommand reads it from there. Prefer that to `--api-key`: a
command-line value, even `--api-key=$VAR`, is visible in `ps`.

### Deploy: `rbt cloud up`

```sh
export REBOOT_CLOUD_API_KEY=<your-key>
rbt cloud up \
  --application-name=my-app \
  --organization=my-org \
  --size=xsmall
```

- `--application-name` names the app inside the organization; later
  `cloud` subcommands use the same value.
- `--organization` — pass it on **every** `rbt cloud` command. Without
  it the app is looked up under your user, not the organization, and
  a new app cannot be created without it. Creating an app needs a
  valid payment method on the organization.
- `--size`: `xsmall` (default), `small`, `medium`, `large`, `xlarge`.
- `--dockerfile=./Dockerfile` (default); `--docker-build-arg=KEY=VALUE`
  (repeatable) forwards build args.

On success it prints three URLs:

```text
  Your API is available at:      https://<application-id>.prod1.rbt.cloud:9991
  MCP clients can connect at:    https://<application-id>.prod1.rbt.cloud:9991/mcp
  You can inspect your state at: https://<application-id>.prod1.rbt.cloud:9991/__/inspect
```

`/__/inspect` is the production twin of the local inspect page. For the
same state from the terminal, run `rbt inspect` against the API URL
([inspect skill](../../inspect/SKILL.md)). To update, run `rbt cloud
up` again: it rolls a new revision forward.

### Secrets, logs, teardown

- **Secrets**: `rbt cloud secret set/list/delete` —
  [`lifecycle-secrets.md`](lifecycle-secrets.md). Run the first `up`
  before the first `secret set`.
- **Logs**: `rbt cloud logs` streams the app's logs; `--follow` tails,
  `--revisions=` filters by revision.
- **Teardown**: `rbt cloud down --application-name=... --organization=...
  --expunge` deletes the application's state (see Limits).

### Auth

Every externally reachable method needs an authorizer before deploying.
Calls without one are **denied** (`PermissionDenied`) on Cloud, as under
`rbt serve`; `rbt dev run` allows them with a 60-second warning, so the
gap shows only on first deploy. See
[`servicer-authorizer.md`](servicer-authorizer.md) and
[`auth-allow-if.md`](auth-allow-if.md).

## Never

- **`rbt cloud down` to roll back or pause** — at 1.6.0 it always
  expunges state; `--no-expunge` is refused. Roll forward with
  another `rbt cloud up`.
- **`rbt cloud down --expunge` to change size** — resizing is
  non-destructive (see Limits).
- **Dropping `--organization` after the first deploy** — the command
  then reports that the application does not exist.
- **`--api-key=<key>` on the command line** — use
  `REBOOT_CLOUD_API_KEY`.

## Limits

- **`rbt cloud down` always deletes state** at 1.6.0 (source: it fails
  without `--expunge`). Secrets survive it
  ([`lifecycle-secrets.md`](lifecycle-secrets.md)). The only way to
  keep data across it, or across a breaking-change expunge, is
  `rbt export` / `rbt import` (`rbt export --help`); the
  [inspect skill](../../inspect/SKILL.md) mentions them.
- **Changing `--size` keeps state**: `rbt cloud up` at a new size rolls
  a new revision forward like any redeploy (confirmed by Reboot,
  reboot-crm).
- **`rbt cloud up` returns before the app serves**: `/__/inspect`
  answered 503 for about 30 seconds after `up` exited 0. A 503 that
  carries `access-control-allow-origin` means "still rolling out", not
  "misconfigured" (reboot-crm, 1.6.0).
- **The image push needs `/var/run/docker.sock`**. Stock Docker Desktop
  on macOS does not create it (its socket is
  `~/.docker/run/docker.sock`), so the push fails even though `docker`
  works. Before `rbt cloud up`:
  `export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"`
  (reboot-crm, 1.6.0).
- **An `oauth=` app needs `allowed_origins`** in production; the
  default is refused at boot. The [`deploy` skill](../../deploy/SKILL.md)
  covers what to list.

## Scales as

- Horizontal: Cloud partitions actors across machines automatically;
  `rbt serve` scales only vertically (framework design).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `--organization=... is required for new applications` | `cloud up` without `--organization`, for a new app or for an org app looked up under your user | Add `--organization=<org>` |
| `User '...' does not have an application named '...'. If the application belongs to an organization, try adding --organization=<name>.` | `--organization` left off `down` / `logs` / `secret`; the app exists | Add `--organization=<org>` |
| `Currently all applications brought down are expunged.` | `rbt cloud down --no-expunge` | There is no non-destructive down; export first if you need the data |
| `Organization '...' does not have a valid payment method.` | Creating an app on an org with no payment method | Add one at `cloud.reboot.dev` |
| `push failed: failed to connect to the docker API at unix:///var/run/docker.sock` | macOS Docker Desktop socket is elsewhere | `export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"` |
| `Could not deploy revision` | The new revision failed to start; its logs follow | Fix the cause in the logs and `up` again |
| `` `OAuth` requires `allowed_origins=[...]` to be set explicitly in production `` | `oauth=` with no `allowed_origins` outside `rbt dev run` | List the SPA's origin, or `allowed_origins=[]` for same-origin only |
| `PermissionDenied` | A method with no authorizer, allowed in dev, denied here | Add an authorizer |

## See also

- [`lifecycle-dockerfile.md`](lifecycle-dockerfile.md) — the image `up` builds
- [`lifecycle-secrets.md`](lifecycle-secrets.md) — Cloud secrets and ordering
- [`../../deploy/SKILL.md`](../../deploy/SKILL.md) — frontend, domain, `allowed_origins`
