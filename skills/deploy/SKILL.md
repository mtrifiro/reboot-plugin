---
name: deploy
description: Deploy a finished Reboot app to production. Use when the user asks to deploy, ship, go live or publish. The backend goes on Reboot Cloud and the web frontend, if any, to a static host (Cloudflare Pages) under the user's own domain, calling the backend cross-origin. Every deploy runs the project's `scripts/deploy.sh` (a pushed commit, an additive API, the revision serving, the live bundle); the first deploy also sets up the Pages project, the domain and `OAuth(allowed_origins=...)`.
argument-hint: [<project-directory>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit, AskUserQuestion
---

# deploy — Put a Reboot App in Production

> **Version notices:** if `rbt` reports a version mismatch or a newer
> Reboot, follow the [upgrade skill](../upgrade/SKILL.md).

Put a working app on the internet: the backend on **Reboot Cloud**, the
web frontend (a React SPA) on a **static host** (here Cloudflare Pages)
at the user's **own domain**. They talk cross-origin: the SPA calls
`https://<application-id>.<cell>.rbt.cloud:9991` directly, allowed by
`OAuth(allowed_origins=[...])`. This skill changes only production
configuration; to build see the [`app` skill](../app/SKILL.md); to run
locally, the [run skill](../run/SKILL.md).

**Every deploy is `scripts/deploy.sh`.** It ships a pushed commit, never
a working tree, and stops at the first thing wrong:

1. The tree is clean, on the production branch, and pushed.
2. The API change since the commit production runs is additive
   (`scripts/api_removals.py`); a removal needs an expunge and a
   restore, which it never does
   (`python/references/lifecycle-backup-restore.md`).
3. Backend, when `backend/`, `api/`, `.rbtrc` or the `Dockerfile`
   changed: `deploy/before-backend` (the templates' backs production
   up with `scripts/backup.sh prod`, and a failed backup stops the
   deploy), `rbt cloud up` with the app's name and size, and a wait
   until the new revision serves.
4. Frontend: built from the commit in a scratch copy, published with
   wrangler, and the live site checked to serve the new bundle.
5. A line in `deploy/ledger.jsonl` (commit, revision, bundle), committed
   and pushed: what step 2 checks against next time. Its `release`
   field is the **release record**: the commits, the model diff and the
   last test run since the previous deploy, also printed before anything
   ships ([`build/references/evidence.md`](../build/references/evidence.md)).

A deploy is the Reboot Flywheel's **promote** decision, the user's
([`build/references/flywheel.md`](../build/references/flywheel.md)):
show them the dry run's model diff and test line, and say plainly when
the last run was not a clean, full, passing run of this commit. On
another branch, say what isn't merged into the production branch yet
and ask whether to merge it first; never merge or switch on your own.

Steps 1–7 below are the first deploy. After it, a deploy is
`scripts/deploy.sh --dry-run` (show the user what would ship), then
`scripts/deploy.sh`. The dry run's output comes with the "Ready to
deploy" card and Step 7's checks end with "Live"
([`build/references/flywheel.md`](../build/references/flywheel.md),
"Stage cards"): in full the first time, one line after.

## When to Use

- A finished Web App (or a dual-frontend app's web frontend) should go
  live on the user's domain.
- An MCP UI with **no** web frontend: Steps 1–3 only — MCP UIs ship in
  the backend image and are served by the backend.
- Any later deploy: run the script (Options below).

## Step 1 — Gather inputs (ask early, in one pass)

Ask for all of this up front (one `AskUserQuestion` round or message):

1. **The frontend's domain** (e.g. `app.example.com`) and whether its
   DNS is on Cloudflare; the hostname must be attachable to the static
   host.
2. **Cloudflare credentials** for headless publishing:
   `CLOUDFLARE_ACCOUNT_ID` and a `CLOUDFLARE_API_TOKEN` with Cloudflare
   Pages: Edit, Zone: Read, and DNS: Edit (DNS only if the zone is on
   Cloudflare).
3. **Reboot Cloud access**: `REBOOT_CLOUD_API_KEY`, the organization, an
   application name and size — see
   `python/references/lifecycle-reboot-cloud.md`.

The credentials go in `.deploy.env` at the project root, which the
script reads and git ignores; never on a command line (visible in the
process listing):

```sh
REBOOT_CLOUD_API_KEY=...
REBOOT_CLOUD_ORGANIZATION=...
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=...
```

## Step 2 — Install and configure the deploy script

A project from the build templates has `scripts/deploy.sh`,
`scripts/api_removals.py`, the backup scripts (`scripts/backup.sh`,
`restore.py`, `compare_exports.py`, `migrations/`) and `deploy/`. An
older one copies them, and `tests/backup_restore_test.py`, from
`<plugin>/skills/build/templates/<front-door>/` (`mcp-ui`, `web-app` or
`both`); adds `.deploy.env` and `exports/` to `.gitignore`; adds
`scripts` to `.mypy.ini`'s `mypy_path` and `pytest.ini`'s `pythonpath`;
and, before its first restore, sets `restore.py`'s rules
(`python/references/lifecycle-backup-restore.md`). A project with a deploy
script of its own keeps it: say what this one checks, and let the user
choose.

Fill in `deploy/config` (shell, sourced):

| Setting | Meaning | web-app | both | mcp-ui |
|---|---|---|---|---|
| `APP`, `SIZE` | the Cloud application and its size | name, `xsmall` | | |
| `BRANCH` | the branch production runs | `main` | | |
| `FRONTEND_DIR` | where `npm run build` runs | `web` | `frontend` | empty |
| `ENV_DIR` | where `.env.production` goes | `web` | `frontend/web` | |
| `PUBLISH_DIR` | the built site | `web/dist` | `frontend/dist/web` | |
| `PAGES_PROJECT`, `SITE_URL` | the Pages project; the domain once attached | | | |

`APP` and `SIZE` are passed to `rbt cloud up` on every deploy, so a
redeploy can't resize the app by a forgotten flag; `.rbtrc` holds one
application only. Commit `deploy/` and the scripts.

- **`deploy/before-backend`** (run before `rbt cloud up`; a non-zero
  exit stops the deploy) ships backing production up with
  `scripts/backup.sh prod`; add the project's own steps below it.
  `deploy/after` runs last. Both executable; the script runs them if
  present. Backups land in git-ignored `exports/backups/`
  (`python/references/lifecycle-backup-restore.md`).
- **An app already in production**: seed the ledger with the commit it
  runs, so the API check has a base, and its API address, which the
  backup exports from:
  `echo '{"backend_commit": "<sha>", "api_url": "https://<id>.<cell>.rbt.cloud"}' >> deploy/ledger.jsonl`.

## Step 3 — Deploy the backend

The first time, with no ledger: `scripts/deploy.sh --first --backend-only`.
It prints the API address (`https://<application-id>.<cell>.rbt.cloud:9991`)
and records it in the ledger; Step 5 bakes it in. Image:
`python/references/lifecycle-dockerfile.md` (the script stops without a
`Dockerfile`); secrets: `python/references/lifecycle-secrets.md`. What
commonly bites here:

- **Docker Desktop on macOS.** `rbt cloud up` pushes with
  `docker --config <temporary dir> push`, which drops the
  `desktop-linux` context and falls back to `/var/run/docker.sock`
  (1.6.0 source), which stock Docker Desktop doesn't create:
  `failed to connect to the docker API at unix:///var/run/docker.sock`.
  The script exports `DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"`
  when that socket is missing (reboot-crm, 1.6.0).
- **Secrets come after the first `up`.** `rbt cloud secret set` before
  the app exists fails with "Organization '...' does not have an
  application named '...'". The first `rbt cloud up` creates the app
  (unhealthy if it needs its secrets, e.g. `prod=Google(...)` with no
  client id, so the script's wait times out); then `rbt cloud secret
  set` every secret at once, which rolls it out again (see
  `python/references/lifecycle-secrets.md`). Secrets survive
  `rbt cloud down --expunge`, so this bites only on creation
  (reboot-crm, 1.6.0).
- **Pass `--organization` on every `rbt cloud` command** you run by
  hand; without it `rbt cloud down` answers "User '...' does not have an
  application named '...'" for an existing app (reboot-crm, 1.6.0). The
  script always passes it.
- **A real OAuth provider.** `Development()` is dev-only; set `prod=`
  (`mcp-ui/references/auth-oauth-providers.md`: per-provider details,
  incl. registering `/__/oauth/callback` as the IdP redirect URI).
- **Authorizers everywhere**: production denies externally reachable
  methods without one (`python/references/servicer-authorizer.md`).
  The script names every servicer still without one beside the release
  record and records them in the ledger; add them before promoting.
- **Dual-frontend apps:** the image must still run the MCP UI builds so
  `dist/mcp/<name>/` is in it; the **web** SPA need _not_ be (it goes to
  the static host).

## Step 4 — Allow the frontend's origin on the backend

```python
application = Application(
    ...,
    oauth=OAuth(
        provider=...,
        allowed_origins=["https://app.example.com"],
    ),
)
```

- Entries are exact origins — `scheme://host[:port]`, no trailing slash
  or path. List **every** origin served (e.g. `https://example.com` and
  `https://www.example.com` if both resolve, and
  `https://<project>.pages.dev` if wanted).
- This one list drives both Reboot Cloud's proxy CORS policy **and**
  OAuth redirect validation (`/__/oauth/start?return_to=...` accepts
  only listed origins); no separate OAuth configuration.
- In production an app with `oauth=` **must** set `allowed_origins`
  (empty list is fine with no browser frontend), or startup fails.

Commit, push, and `scripts/deploy.sh --backend-only`.

## Step 5 — Set up the production frontend build

Detect the layout (as the [run skill](../run/SKILL.md) does):

- **Standalone Web App** — one SPA, stock Vite config, `index.html` at
  the top of the SPA directory (e.g. `web/`); default `base: "/"`.
- **Dual-frontend** — `frontend/vite.config.ts` builds
  `RBT_BUILD_TARGET=mcp:<name>` targets and an `RBT_BUILD_TARGET=web`
  target into `dist/`; the web build uses `base: "/__/frontend/web/"`.

1. **Bake in the backend URL**: in `ENV_DIR`, next to the SPA's dev
   `.env` (which sets `VITE_REBOOT_URL`), write `.env.production` and
   **commit it** (the script builds from the commit and stops without
   it) — Vite's production build reads it; leave `.env` alone:

   ```sh
   VITE_REBOOT_URL=https://<application-id>.<cell>.rbt.cloud:9991
   ```

   Dual-frontend: add the web app's own address in the same file. The
   MCP UIs' builds read it too, so their "Open in web app" link
   (`webAppUrl()`) leaves the backend for the published site:

   ```sh
   VITE_WEB_APP_URL=https://<your custom domain>/
   ```

2. **Add `_redirects`** to the SPA's `public/` (Vite copies it). The
   standard SPA fallback, so a hard load of `/some/route` isn't a 404:

   ```
   /* /index.html 200
   ```

   Dual-frontend: add a line **first** mapping the baked asset prefix
   onto the published files:

   ```
   /__/frontend/web/* /:splat 200
   /* /index.html 200
   ```

3. **Router basename** (e.g. React Router) must be `"/"` or unset. Never
   `basename={import.meta.env.BASE_URL}`: on the dual-frontend layout it
   bakes `/__/frontend/web/` into in-browser route matching, which no
   host rewrite fixes, and every route silently renders nothing on the
   custom domain.

## Step 6 — Create the Pages project, publish, attach the domain

With the Cloudflare credentials exported (`set -a; . ./.deploy.env; set +a`),
`wrangler` runs headless (no `wrangler login`). Create the project once:

```sh
npx --yes wrangler@4 pages project create <PAGES_PROJECT> \
    --production-branch=main
```

Then publish with `scripts/deploy.sh --frontend-only`: it builds, runs
`wrangler pages deploy`, and waits for `https://<PAGES_PROJECT>.pages.dev`
to serve the new bundle. Attach the custom domain via the Cloudflare API
(no wrangler subcommand):

```sh
curl -sS -X POST \
    "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects/<project-name>/domains" \
    -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    -H "Content-Type: application/json" \
    --data '{"name": "app.example.com"}'
```

Point DNS at the project. Zone on Cloudflare: get the zone id with
`GET /zones?name=example.com`, then:

```sh
curl -sS -X POST \
    "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
    -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    -H "Content-Type: application/json" \
    --data '{"type": "CNAME", "name": "app.example.com", "content": "<project-name>.pages.dev", "proxied": true}'
```

Zone **not** on Cloudflare: have the user add
`CNAME app.example.com → <project-name>.pages.dev` at their DNS
provider; the attachment validates once it resolves. Cloudflare
provisions TLS automatically after validation. Then set `SITE_URL` in
`deploy/config` to the domain and commit, so later deploys check the
site people use.

## Step 7 — Verify

The script already waited for the revision to serve (`/__/inspect`
returns 503 for about thirty seconds after `rbt cloud up`; reboot-crm,
1.6.0) and for the site to serve the new bundle. Then:

1. **Static serving:** `curl -sSI https://app.example.com/` and a deep
   route (`curl -sSI https://app.example.com/some/route`) both return
   200 with `content-type: text/html`.
2. **CORS:**

   ```sh
   curl -sSI "https://<application-id>.<cell>.rbt.cloud:9991/__/oauth/whoami" \
       -H "Origin: https://app.example.com"
   ```

   must include `access-control-allow-origin: https://app.example.com`
   and `access-control-allow-credentials: true`; otherwise the Cloud
   backend predates the `allowed_origins` change — redeploy.
3. **In the browser** (user or browser tool): open
   `https://app.example.com`, sign in (bounces through `/__/oauth/start`
   and back), confirm signed-in live data renders — proving the
   cross-origin WebSocket path.

## Options

```sh
scripts/deploy.sh --dry-run        # every check, and what would ship; nothing deployed
scripts/deploy.sh                  # backend if what it serves changed, then frontend
scripts/deploy.sh --backend-only   # or --frontend-only
scripts/deploy.sh --first          # the first deploy: no ledger yet
```

- **An API removal Reboot allows** (an `mcp=` option, a field's
  `description=`; `python/references/api-schema-evolution.md`) ships
  only when `deploy/api-exceptions.md` names it, file and exact line;
  delete the entry once shipped. Any other removal needs an expunge and
  a restore: stop and tell the user, then follow
  `python/references/lifecycle-backup-restore.md` (back up, expunge,
  boot, restore, boot, compare) with them.
- The script refuses a dirty tree, another branch, or an unpushed
  commit: commit and push first, never work around it.

## Troubleshooting

- **Blank page, MIME-type or 404 asset errors:** asset prefix doesn't
  match the host — on dual-frontend, the `/__/frontend/web/*` line is
  missing from `_redirects` or isn't first.
- **Routes render nothing on the custom domain but `/` loads:** basename
  from `import.meta.env.BASE_URL` (Step 5.3).
- **CORS errors in the console:** exact origin (scheme, `www.`) missing
  from `allowed_origins`, or the backend not redeployed after.
- **Sign-in fails with an invalid-redirect error:** same cause —
  `/__/oauth/start` refuses the `return_to`.
- **"did not serve within five minutes":** the revision is unhealthy;
  `rbt cloud logs --revisions=<n>` (the script prints the command). On
  creation, usually missing secrets (Step 3).
- **"still serves ... after a minute":** the publish went to another
  branch or project, or `SITE_URL` names a domain not attached yet.
- **Local Safari sign-in fails with `Missing pending-flow cookie`:**
  dev-only; see
  [`run/references/stop-restart-reset.md`](../run/references/stop-restart-reset.md)
  § "Errors you will see".
- **Session doesn't survive a reload in Safari/Firefox:** tracking
  prevention can strip the cross-site session cookie silent restoration
  needs; the user signs in again. A known limit of fully cross-site
  hosting.
