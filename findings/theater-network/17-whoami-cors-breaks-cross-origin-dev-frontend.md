---
id: theater-network-17
project: theater-network
source: "theater-network/docs/reboot-findings.md §17"
reboot_version: 1.4.0
severity: unrated
target: framework
names:
  - web-app/references/react-client.md
tags: [frontend, auth, version-drift]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# 1.4.0: /__/oauth/whoami CORS breaks every cross-origin dev frontend

**What happened.** The 1.4.0 `@reboot-dev/reboot-react` client probes `/__/oauth/whoami` with `credentials: "include"` before settling auth state. The 1.4.0 dev server's response (a 404 on an app with no `oauth=`) carries `access-control-allow-origin` but NOT `access-control-allow-credentials: true`, which a credentialed fetch requires. The browser discards the response, the client never sees the 404 that would settle it unauthenticated, and retries on exponential backoff forever. Every Vite-on-:5173 / backend-on-:9991 dev setup hits this: seconds of delay on every page's data plus a console full of CORS errors. Workaround used: serve same-origin (Vite proxies `/__/` with `ws: true`, and `/theater.v1.` to `:9991`, and the client URL defaults to `window.location.origin`). Reported upstream.

**Expected.** Not recorded.

**Repro.** Vite dev server on :5173 with backend on :9991, app with no `oauth=`, 1.4.0.

**Where in the skills.** Not a skill gap unless the bug persists; `web-app/references/react-client.md` covers backend URL in dev.

**Checked at 1.6.0.** Not checked against the 1.6.0 runtime. `web-app/references/react-client.md:227` mentions the whoami probe only as an `isLoading` note.
