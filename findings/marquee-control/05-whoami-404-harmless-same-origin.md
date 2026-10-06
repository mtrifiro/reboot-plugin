---
id: marquee-control-05
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 5"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - web-app/references/react-client.md
tags: [frontend, auth]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# whoami on a no-oauth app 404s harmlessly through a same-origin proxy on 1.4.1

**What happened.** Through the same-origin proxy the `/__/oauth/whoami` probe 404s twice at boot, then the client stops. The 1.4.0 cross-origin failure mode was different: the CORS-discarded response is indistinguishable from a network error, so the client retried forever. Same-origin proxy remains the right default on 1.4.1.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `web-app/references/react-client.md`. The 1.4.0 failure is theater-network-17; actor-flight-02 reports the cross-origin console error at 1.5.0.

**Checked at 1.6.0.** `web-app/references/react-client.md` mentions the whoami probe only as the `isLoading` gate; grep for `proxy`/`same-origin` in `web-app/` found nothing, so the same-origin setup is not taught.
