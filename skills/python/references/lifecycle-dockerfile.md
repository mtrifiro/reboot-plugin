---
title: Write a Reboot Cloud Dockerfile
impact: HIGH
impactDescription: Reboot Cloud rejects images that don't follow this layout; mistakes only surface on first deploy.
tags: dockerfile, deploy, rbt-cloud, base-image, codegen, dockerignore
summary: "The Dockerfile layout Reboot Cloud accepts, backend-only or with a bundled MCP UI frontend; production flags belong in `.rbtrc` `serve run` lines, not the Dockerfile; `.dockerignore`."
step: deploy
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Write a Reboot Cloud Dockerfile

## When you are here

You are about to run `rbt cloud up` (or build an image for a
self-hosted `rbt serve`) and need the project-root `Dockerfile` and
`.dockerignore`. The deploy commands are in
[`lifecycle-reboot-cloud.md`](lifecycle-reboot-cloud.md); the `.rbtrc`
format is in [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md).

## Do this

Three non-negotiables: the base image is
`ghcr.io/reboot-dev/reboot-base:<version>` with `<version>` equal to the
`reboot==<version>` pin; `CMD ["rbt", "serve", "run"]` with every
production flag in `.rbtrc`; and layer order deps → schema + `.rbtrc`
→ `rbt generate` → (optional) frontend build → `backend/src/` → `CMD`.

### Backend-only

Verbatim from
[the `reboot-hello` example](https://github.com/reboot-dev/reboot-hello/blob/main/Dockerfile).
The version literal appears only here, so `make versions` can rewrite
it:

```dockerfile
FROM ghcr.io/reboot-dev/reboot-base:1.6.0

WORKDIR /app

# First ONLY copy and install the requirements, so that changes outside
# `requirements.txt` don't force a re-install of all dependencies.
COPY requirements.lock requirements.txt
RUN pip install -r requirements.txt

# Next, copy the API definition and generate Reboot code. This step is also
# separate so it is only repeated if the `api/` code changes.
COPY api/ api/
COPY .rbtrc .rbtrc

# Run the Reboot code generators. We did copy all of `api/`, possibly
# including generated code, but it's not certain that `rbt generate` was run in
# that folder before this build was started.
RUN rbt generate

# Now copy the rest of the source code.
COPY backend/src/ backend/src/

CMD ["rbt", "serve", "run"]
```

### With a bundled frontend (MCP UIs)

When the Reboot backend also serves the embedded UI's static files, add
two layers:

```dockerfile
# After `COPY .rbtrc`, before `RUN rbt generate`:
COPY frontend/ frontend/

# Standard rbt codegen — generates `backend/api/` AND `frontend/api/`.
RUN rbt generate

# Build the React UIs into `frontend/dist/`. For MCP apps the Reboot app
# itself is also the static web server, so it needs these static
# assets.
RUN cd frontend && npm ci && npm run build

# Then the existing `COPY backend/src/ backend/src/` and `CMD ...`.
```

`COPY frontend/` comes **before** `RUN rbt generate`: the generator
writes fresh bindings into `frontend/api/`, and copying `frontend/`
afterwards would clobber them with any stale local copy.

### The production lines in `.rbtrc`

```sh
# Tell `rbt serve` this is a Python application.
serve run --python

# If the app bundles a frontend (built to `frontend/dist/`), serve it
# at `/__/frontend/` from the built-in HTTP server.
serve run --frontend-dist-path=frontend/dist --frontend-root-path=frontend

# Entry point.
serve run --application=backend/src/main.py

# Persist state under this name (also used by `rbt cloud {up,down,logs}`).
serve run --application-name=<app>

# Reboot Cloud terminates TLS at the load balancer.
serve run --tls=external
```

### `.dockerignore`

Derived from
[the `reboot-agent-wiki` example](https://github.com/reboot-dev/reboot-agent-wiki/blob/main/.dockerignore).
Backend-only:

```gitignore
# Python runtime caches and venv — rebuilt inside the image.
.venv/
__pycache__/
*.py[cod]
.mypy_cache/
.pytest_cache/

# Reboot runtime state (dev-only).
.rbt/

# Generated code — regenerated inside the image by `rbt generate`.
backend/api/

# No web frontend in this image.
web/

# VCS.
.git/
.gitignore

# Editor / OS.
.vscode/
.idea/
*.swp
.DS_Store

# Local-only files.
README.md
```

Bundled frontend: the same file, with `web/` replaced by these lines
so the sources `npm ci && npm run build` needs stay in the context:

```gitignore
# Generated code — regenerated inside the image.
frontend/api/

# Node deps + build output — rebuilt inside the image.
frontend/node_modules/
frontend/dist/
```

## Never

- **`CMD ["rbt", "dev", "run"]` in a Cloud image** — dev defaults (no
  `--tls=external`, dev-mode auth, watcher loops) are wrong for
  production. Always `serve run`.
- **A base image version different from the `reboot==` pin** — the
  image bakes in a specific `rbt` CLI and runtime; a mismatch surfaces
  as obscure protocol or codegen errors on first deploy.
- **`RUN rbt generate` before `COPY frontend/`** (bundled variant) —
  the stale local `frontend/api/` overwrites the fresh bindings.
- **Production flags on the `CMD` line** — it works, but truth is
  split across two files. `CMD` is exactly `["rbt", "serve", "run"]`.
- **A hand-rolled non-Reboot base image** — reinstalling the `rbt`
  CLI correctly (version, binary location, system deps) is
  non-trivial. Use `reboot-base`.
- **No `serve run --application-name=<app>`** — Cloud uses it to
  identify the app across deploys; without it the first `cloud up`
  works but state persistence gets surprising. (`--name` is the
  deprecated alias and warns.)
- **`COPY backend/src/` near the top** — every backend edit then
  reinstalls dependencies.

## Limits

- Docker rebuilds from the first changed `COPY`/`RUN` down. In the
  layout above a `backend/src/` edit rebuilds only the last `COPY`
  and `CMD`; an `api/` or `.rbtrc` edit reruns `rbt generate` and
  everything after it; a lockfile change reinstalls dependencies.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Could not find Dockerfile '...'` | `rbt cloud up` looked for `./Dockerfile` (or `--dockerfile=`) and found nothing | Add it at the project root, or pass `--dockerfile=` |

## See also

- [`lifecycle-reboot-cloud.md`](lifecycle-reboot-cloud.md) — `rbt cloud up` and friends
- [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md) — `serve run` line syntax
- [`../../deploy/SKILL.md`](../../deploy/SKILL.md) — end-to-end production deploy
