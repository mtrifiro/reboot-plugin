---
id: reboot-crm-30
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P2.1"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/react-generated-client.md
  - python/references/servicer-reader.md
tags: [negative-space, pattern, frontend, cost]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# Transitive reactivity is real but undocumented

**What happened.** The app subscribed to one reader per actor (141 WebSocket streams for the People page) because the references only say "when any session mutates the state, every mounted reader re-renders" (`react-generated-client.md`), which reads as that actor's state. Only by reading `reboot/aio/state_managers.py::reactively` and `contexts.py::React` did the author learn that a subscribed reader that calls readers on other actors is re-run when any of them changes. Switching to one `Pipeline.board` / `Pipeline.people` reader cut subscriptions to one per page.

**Expected.** A sentence in `react-generated-client.md` and `servicer-reader.md`: a subscribed reader is transitively reactive (re-runs when any state it read, through other actors' readers including `forall`, changes); prefer one aggregating reader over N subscriptions; with the caveats from `reactively` (unary readers only, dependency set re-tracked per execution, backoff polling on error). Documentation only. Pair with the design rule in reboot-crm-31.

**Repro.** Not recorded.

**Where in the skills.** `python/references/react-generated-client.md`, `python/references/servicer-reader.md`.

**Checked at 1.6.0.** Neither file mentions transitive reactivity (grep for `transitive` in those files and `web-app/`).
