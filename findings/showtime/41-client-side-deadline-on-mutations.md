---
id: showtime-41
project: showtime
source: "2026.08.18 reboot-findings.md #41"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
  - web-app/references/react-client.md
tags: [pattern, frontend, operations]
cluster: "E"
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-react-state.md § Do this"
---

# Always put a client-side deadline on mutations in a dev-loop UI

**What happened.** `rbt dev run --watch` restarts the app on every backend save; a call in flight during a restart can leave a browser promise unresolved (external-context calls retry transport failures rather than failing fast). Racing each call against a ~20s timeout turns that into an honest 'backend didn't answer, nothing is corrupted, try again' instead of a permanently spinning button.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded; frontend references.

**Checked at 1.6.0.** grep for `deadline`/`timeout`/`watch` restart guidance in web-app, mcp-ui and python references found nothing relevant.
