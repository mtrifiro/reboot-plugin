---
id: reboot-crm-29
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.19"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - run/SKILL.md
  - web-app/SKILL.md
  - deploy/SKILL.md
tags: [auth, operations, error-text, frontend]
cluster: "4.2"
still_applies: yes
status: Open
resolved_by: ""
---

# The dev OAuth server sets Secure on cookies served over plain http, so local sign-in fails in every WebKit browser

**What happened.** Signing in to the local app (Vite on one localhost port, backend on another) from Safari on macOS ends on a JSON page: `{"error":"invalid_request","error_description":"Missing pending-flow cookie. The sign-in flow may have expired; try signing in again."}`; retrying does the same, and a WKWebView browser fails identically. The first hop (`/__/oauth/start`) sets `rbt_oauth_pending=<jwt>; HttpOnly; Max-Age=600; Path=/__/oauth/; SameSite=lax; Secure` over `http://`; WebKit does not store a `Secure` cookie arriving over http and makes no exception for `localhost`. Session cookies (`rbt_session`, `rbt_refresh`) carry `SameSite=none; Secure` too. Chrome and Firefox were not tested but are expected to work. Replaying the flow with curl and passing the pending cookie by hand reaches `finish` and gets the 302 with session cookies. The error text points at an expired flow, so the author retried and checked `allowed_origins` first; the deploy skill's Safari note describes a different, production-only symptom.

**Expected.** Fix proposed: (1) derive cookie flags from the request: https keeps `SameSite=none; Secure`, plain http (loopback under `rbt dev run`) omits `Secure` and uses `SameSite=lax`; (2) when `finish` finds no pending cookie over plain http, say so instead of "the flow may have expired"; (3) `run/SKILL.md` and the `web-app` skill note that local sign-in in Safari/WKWebView needs the backend over TLS (`--tls-certificate`, `--tls-key`, mkcert) or a Chromium/Firefox browser. Recommendation: (1), plus (2) regardless.

**Repro.** Run under `rbt dev run` (no TLS flags), open `http://localhost:<vite port>` in Safari, click sign in, pick an identity. Without a browser: `curl -sS -D - "http://localhost:9989/__/oauth/finish?code=x&state=y"` returns 400 with the same text. Workaround: `mkcert -install; mkcert localhost 127.0.0.1`, pass `--tls-certificate`/`--tls-key` (can live in `.rbtrc`), set `VITE_REBOOT_URL=https://localhost:9989`; or use Chrome.

**Where in the skills.** `run/SKILL.md`, `web-app/SKILL.md` (no note on local sign-in in WebKit).

**Checked at 1.6.0.** No mention of WebKit, mkcert or `--tls-certificate` in `run/SKILL.md` or `web-app/SKILL.md` (grep); `deploy/SKILL.md` has a Safari note about production only.
