---
id: actor-flight-02
project: actor-flight
source: "reboot-findings.md §2"
reboot_version: 1.5.0
severity: unrated
target: framework
names: []
tags: [frontend, auth, error-text]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# RebootClientProvider probes /__/oauth/whoami even when the app has no OAuth

**What happened.** An app built without `oauth=` still gets a browser console error on every load: the client fetches `/__/oauth/whoami` and the response has no `Access-Control-Allow-Origin` for the Vite origin. Nothing breaks (`useUser` is not used) but it reads as a failure.

**Expected.** Skip the probe when the app reports no OAuth server, or have the endpoint answer CORS like the RPC routes.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
