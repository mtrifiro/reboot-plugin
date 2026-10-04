---
id: theater-network-21
project: theater-network
source: "theater-network/docs/reboot-findings.md §21"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - run/SKILL.md
  - web-app/references/react-client.md
tags: [operations, frontend]
cluster: "F"
still_applies: yes
status: Resolved
resolved_by: "python/references/lifecycle-dev-loop.md § Never"
---

# After an expunge, open tabs are haunted; reload them

**What happened.** An expunge deletes every actor and a reseed recreates SOME of them under the same ids. Tabs open across the boundary split personality: subscriptions to recreated actors (showings, seats) resume as their `StateNotConstructed` retries start succeeding, while subscriptions to lazily-constructed actors (carts, which exist only once touched) retry forever and freeze at their last pre-expunge frame. The result is convincingly weird (a live seat map beside a cart panel listing purchases from a deleted world) and cost a full debugging pass because the pane looked current. Extends item 9.

**Expected.** Operational rule from the source: every open tab reloads after every expunge; the reload re-touches the cart and opens fresh streams.

**Repro.** Expunge, reseed, keep a tab open.

**Where in the skills.** `run/SKILL.md` Stop / restart / reset section.

**Checked at 1.6.0.** No expunge-then-reload-tabs guidance in `run/SKILL.md` or `web-app/`.
