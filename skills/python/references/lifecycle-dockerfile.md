---
title: Write a Reboot Cloud Dockerfile
impact: HIGH
impactDescription: Reboot Cloud rejects images that don't follow this layout; mistakes only surface on first deploy.
tags: dockerfile, deploy, rbt-cloud, base-image, codegen, dockerignore
summary: "Production flags belong in `.rbtrc` `serve run` lines, not the Dockerfile; the layout Reboot Cloud accepts; `.dockerignore`."
step: deploy
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Write a Reboot Cloud Dockerfile

## When you are here

You need the project-root `Dockerfile` and `.dockerignore` for
`rbt cloud up` or a self-hosted `rbt serve` image. Deploy commands:
[`lifecycle-reboot-cloud.md`](lifecycle-reboot-cloud.md); `.rbtrc`
format: [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md).

## Do this

- Base image `ghcr.io/reboot-dev/reboot-base:<version>`, `<version>`
  equal to the `reboot==<version>` pin.
- `CMD ["rbt", "serve", "run"]`; every production flag in `.rbtrc`.
- Layer order: deps → schema + `.rbtrc` → `rbt generate` → (optional)
  frontend build → `backend/src/` → `CMD`.

### Backend-only

Verbatim from
[`reboot-hello`](https://github.com/reboot-dev/reboot-hello/blob/main/Dockerfile);
the version literal appears only here so `make versions` can rewrite it:

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

When the backend also serves the embedded UI's static files, add two
layers:

```dockerfile
# After `COPY .rbtrc`, before `RUN rbt generate`:
COPY frontend/ frontend/

# Generates `backend/api/` AND `frontend/api/`.
RUN rbt generate

# Build the React UIs into `frontend/dist/`; the Reboot app serves them.
RUN cd frontend && npm ci && npm run build

# Then the existing `COPY backend/src/ backend/src/` and `CMD ...`.
```

### The production lines in `.rbtrc`

```sh
serve run --python
# Only with a bundled frontend: serves frontend/dist at /__/frontend/.
serve run --frontend-dist-path=frontend/dist --frontend-root-path=frontend
serve run --application=backend/src/main.py
# State name; also used by `rbt cloud {up,down,logs}`.
serve run --application-name=<app>
# Reboot Cloud terminates TLS at the load balancer.
serve run --tls=external
```

### `.dockerignore`

Derived from
[`reboot-agent-wiki`](https://github.com/reboot-dev/reboot-agent-wiki/blob/main/.dockerignore).
Backend-only:

```gitignore
.venv/
__pycache__/
*.py[cod]
.mypy_cache/
.pytest_cache/
# Dev-only runtime state; codegen is rerun in the image; no web frontend.
.rbt/
backend/api/
web/
.git/
.gitignore
.vscode/
.idea/
*.swp
.DS_Store
README.md
```

Bundled frontend: replace `web/` with these, keeping the sources
`npm ci && npm run build` needs in the context:

```gitignore
frontend/api/
frontend/node_modules/
frontend/dist/
```

## Never

- **`CMD ["rbt", "dev", "run"]` in a Cloud image** — dev defaults (no
  `--tls=external`, dev-mode auth, watcher loops) are wrong for
  production.
- **A base image version different from the `reboot==` pin** — the
  image bakes in a specific `rbt` CLI and runtime; a mismatch surfaces
  as obscure protocol or codegen errors on first deploy.
- **`RUN rbt generate` before `COPY frontend/`** (bundled) — copying
  `frontend/` after the generator clobbers its fresh `frontend/api/`
  bindings with the stale local copy.
- **Production flags on the `CMD` line** — works, but splits truth
  across two files.
- **A hand-rolled non-Reboot base image** — reinstalling the `rbt` CLI
  correctly (version, binary location, system deps) is non-trivial.
- **No `serve run --application-name=<app>`** — Cloud identifies the
  app across deploys by it; without it the first `cloud up` works but
  state persistence gets surprising. (`--name` is the deprecated alias
  and warns.)
- **`COPY backend/src/` near the top** — every backend edit reinstalls
  dependencies.

## Limits

- Docker rebuilds from the first changed `COPY`/`RUN` down: a
  `backend/src/` edit rebuilds only the last `COPY` and `CMD`; an `api/`
  or `.rbtrc` edit reruns `rbt generate` onward; a lockfile change
  reinstalls dependencies.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Could not find Dockerfile '...'` | `rbt cloud up` looked for `./Dockerfile` (or `--dockerfile=`) and found nothing | Add it at the project root, or pass `--dockerfile=` |
| `issubclass() arg 1 must be a class` from `rbt generate` in the Cloud build | The image runs Python 3.10; a quoted forward reference or 3.11+ syntax in `api/` | `scripts/api_lint.py` finds it; define Models above their use, unquoted |

## See also

- [`lifecycle-reboot-cloud.md`](lifecycle-reboot-cloud.md) — `rbt cloud up` and friends
- [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md) — `serve run` line syntax
- [`../../deploy/SKILL.md`](../../deploy/SKILL.md) — end-to-end production deploy
