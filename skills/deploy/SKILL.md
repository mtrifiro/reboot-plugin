---
name: deploy
description: Deploy a finished Reboot app to production — the backend on Reboot Cloud, and the web frontend (if the app has one) published to a static host (Cloudflare Pages) under the user's own custom domain, talking to the backend cross-origin. Covers the production frontend build (backend URL, SPA fallback, asset paths), publishing with wrangler, attaching the domain, and the Application(allowed_origins=...) configuration that lets the browser reach the backend.
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
configuration; to build see the [`mcp-ui` skill](../mcp-ui/SKILL.md) and
the [web-app skill](../web-app/SKILL.md); to run locally, the
[run skill](../run/SKILL.md).

## When to Use

- A finished Web App (or a dual-frontend app's web frontend) should go
  live on the user's domain.
- An MCP UI with **no** web frontend: do Step 2 only — MCP UIs ship in
  the backend image and are served by the backend.

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
   application name — see `python/references/lifecycle-reboot-cloud.md`.

Export secrets as environment variables, never command-line flags
(visible in the process listing).

## Step 2 — Deploy the backend to Reboot Cloud

Follow `python/references/lifecycle-reboot-cloud.md` (image:
`python/references/lifecycle-dockerfile.md`; secrets:
`python/references/lifecycle-secrets.md`). What commonly bites here:

- **Docker Desktop on macOS.** `rbt cloud up` pushes with
  `docker --config <temporary dir> push`, which drops the
  `desktop-linux` context and falls back to `/var/run/docker.sock`
  (1.6.0 source), which stock Docker Desktop doesn't create:
  `failed to connect to the docker API at unix:///var/run/docker.sock`.
  Export `DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"` first
  (reboot-crm, 1.6.0).
- **Secrets come after the first `up`.** `rbt cloud secret set` before
  the app exists fails with "Organization '...' does not have an
  application named '...'". The first `rbt cloud up` creates the app
  (unhealthy if it needs its secrets, e.g. `prod=Google(...)` with no
  client id); then `rbt cloud secret set` every secret at once, which
  rolls it out again (see `python/references/lifecycle-secrets.md`).
  Secrets survive `rbt cloud down --expunge`, so this bites only on
  creation (reboot-crm, 1.6.0).
- **Pass `--organization` on every `rbt cloud` command**; without it
  `rbt cloud down` answers "User '...' does not have an application
  named '...'" for an existing app (reboot-crm, 1.6.0).
- **A real OAuth provider.** `Development()` is dev-only; set `prod=`
  (`mcp-ui/references/auth-oauth-providers.md`: per-provider details,
  incl. registering `/__/oauth/callback` as the IdP redirect URI).
- **Authorizers everywhere**: production denies externally reachable
  methods without one (`python/references/servicer-authorizer.md`).
- **Dual-frontend apps:** the image must still run the MCP UI builds so
  `dist/mcp/<name>/` is in it; the **web** SPA need _not_ be (it goes to
  the static host).

Record the API URL `rbt cloud up` prints
(`https://<application-id>.<cell>.rbt.cloud:9991`); Step 4 bakes it in.

## Step 3 — Allow the frontend's origin on the backend

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

Then redeploy: `rbt cloud up`.

## Step 4 — Build the frontend for production

Detect the layout (as the [run skill](../run/SKILL.md) does):

- **Standalone Web App** — one SPA, stock Vite config, `index.html` at
  the top of the SPA directory (e.g. `web/`); default `base: "/"`.
- **Dual-frontend** — `frontend/vite.config.ts` builds
  `RBT_BUILD_TARGET=mcp:<name>` targets and an `RBT_BUILD_TARGET=web`
  target into `dist/`; the web build uses `base: "/__/frontend/web/"`.

1. **Bake in the backend URL**: next to the SPA's dev `.env` (which sets
   `VITE_REBOOT_URL`), write `.env.production` — Vite's production build
   reads it; leave `.env` alone:

   ```sh
   VITE_REBOOT_URL=https://<application-id>.<cell>.rbt.cloud:9991
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
4. **Build**: `npm run build` in the frontend directory. The publish
   directory holds the built `index.html` — `web/dist/` (standalone) or
   `frontend/dist/web/` (dual-frontend).

## Step 5 — Publish to Cloudflare Pages and attach the domain

With `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` exported,
`wrangler` runs headless (no `wrangler login`):

```sh
npx --yes wrangler@4 pages project create <project-name> \
    --production-branch=main
npx --yes wrangler@4 pages deploy <publish-directory> \
    --project-name=<project-name> --branch=main
```

The site is live at the printed `https://<project-name>.pages.dev`.
Attach the custom domain via the Cloudflare API (no wrangler
subcommand):

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
provisions TLS automatically after validation. Redeploy with
`wrangler pages deploy` again; project and domain stay.

## Step 6 — Verify

`rbt cloud up` exits 0 before the new revision serves: `/__/inspect`
returned 503 for about thirty seconds after (reboot-crm, 1.6.0), while
CORS headers were already correct (the proxy answers first). Poll first:

```sh
until curl -sf -o /dev/null "https://<application-id>.<cell>.rbt.cloud:9991/__/inspect"; do sleep 5; done
```

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

## Troubleshooting

- **Blank page, MIME-type or 404 asset errors:** asset prefix doesn't
  match the host — on dual-frontend, the `/__/frontend/web/*` line is
  missing from `_redirects` or isn't first.
- **Routes render nothing on the custom domain but `/` loads:** basename
  from `import.meta.env.BASE_URL` (Step 4.3).
- **CORS errors in the console:** exact origin (scheme, `www.`) missing
  from `allowed_origins`, or the backend not redeployed after.
- **Sign-in fails with an invalid-redirect error:** same cause —
  `/__/oauth/start` refuses the `return_to`.
- **503 right after `rbt cloud up`, CORS correct:** still rolling out;
  wait (Step 6).
- **Local Safari sign-in fails with `Missing pending-flow cookie`:**
  dev-only; see
  [`run/references/stop-restart-reset.md`](../run/references/stop-restart-reset.md)
  § "Errors you will see".
- **Session doesn't survive a reload in Safari/Firefox:** tracking
  prevention can strip the cross-site session cookie silent restoration
  needs; the user signs in again. A known limit of fully cross-site
  hosting.
