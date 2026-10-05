---
id: reboot-crm-66
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.27"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - python/references/auth-external-api-calls.md
tags: [auth, negative-space]
cluster: "4.1"
still_applies: unknown
status: Resolved
resolved_by: "python/references/auth-external-api-calls.md § Never"
---

# app_internal=True on an HTTP route matches the request's exact path, so a templated route silently gets an anonymous context

**What happened.** Found by reading source (`reboot/aio/http.py:112` and `:286`), not by being bitten. `HTTP._api_route` records the declared path of a route registered with `app_internal=True` in `_app_internal_paths`, and the middleware hands out the app-internal context when `request.url.path in self._http._app_internal_paths`. A FastAPI route declared `/__/logos/{host}` is registered, serves and its handler is called, but the request path `/__/logos/acme.dev` is never in the set, so the handler gets the ordinary external context with no caller and every app-internal-only call it makes is refused. Workaround: a fixed path with the variable in the query string.

**Expected.** The match made against the route (FastAPI knows which route matched), or registration refusing a templated path with `app_internal=True`, or the DANGER note saying the path must be literal.

**Repro.** Register `application.http.get("/x/{id}", app_internal=True)` with a handler that calls an `INTERNAL`-only method through `external_context(request)`; it is refused.

**Where in the skills.** `python/references/auth-external-api-calls.md` (examples with `app_internal=True` routes).

**Checked at 1.6.0.** `python/references/auth-external-api-calls.md` (lines ~82, 124, 316) uses literal-path `app_internal=True` routes; no warning about path parameters found.
