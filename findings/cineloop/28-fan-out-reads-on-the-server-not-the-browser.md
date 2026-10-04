---
id: cineloop-28
project: cineloop
source: "cineloop/reboot-findings.md §19 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/SKILL.md
  - web-app/references/react-client.md
  - python/references/servicer-reader.md
tags: [cost, pattern, frontend]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# Fan out reads on the server, not in the browser

**What happened.** The lobby's first version gave every showing its own reactive subscription: 12 theaters + 48 showings = 60 live streams on one page. It worked but the last cards took about fifteen seconds to fill and the page was a wall of skeletons. Fix: a `Theater.marquee` reader that calls each of its four showings' `summary` readers server-side and returns four cards in one response; twelve subscriptions instead of sixty, full render in about eight seconds instead of fifteen. A reactive reader that reads other actors stays reactive to those actors (the query tracks every actor it touched); verified in the browser by holding a seat in one tab and watching the lobby count in another go 157 to 155 with no reload.

**Expected.** Source rule of thumb: N reactive subscriptions from one page is a design smell past about 15; if the items share a parent, give the parent a reader that fans out.

**Repro.** Lobby with a subscription per showing (60 streams).

**Where in the skills.** `web-app/SKILL.md`, `web-app/references/react-client.md` (Scales as); `servicer-reader.md`. Also see theater-network-08/23 for the server-side cost of fan-out.

**Checked at 1.6.0.** No subscription-count guidance or server-side fan-out pattern found in `web-app/` or `python/references/react-generated-client.md`; `servicer-reader.md:63` says a reader may call other readers but not that it stays reactive to them.
