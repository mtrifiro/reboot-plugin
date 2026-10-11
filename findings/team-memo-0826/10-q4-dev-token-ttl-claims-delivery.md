---
id: team-memo-0826-10
project: team-memo-0826
source: "2026.08.26 Findings for Reboot Team - Docs, Skills, and Runtime.md Q4"
reboot_version: 1.4.1
severity: unrated
target: framework
names: []
tags: [auth, cost]
cluster: "D"
still_applies: unknown
status: Resolved
resolved_by: "python/references/auth-claims.md § Limits"
---

# Dev access-token TTL and claims delivery

**What happened.** With `Development(claims=["name"])`, how often does `set_claims` re-fire for a long-lived browser session? No problem was seen, but the answer decides whether apps should treat `set_claims` as hot-path.

**Expected.** Source asks for the re-fire frequency.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
