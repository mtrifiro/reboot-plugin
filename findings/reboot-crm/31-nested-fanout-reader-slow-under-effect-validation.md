---
id: reboot-crm-31
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P2.2"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/servicer-reader.md
  - python/references/state-actor-decomposition.md
tags: [cost, pattern, negative-space]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# A reader that fans out to readers that fan out is unusable under effect validation

**What happened.** `Pipeline.journeys` fanned out to `Account.journey` on about a hundred accounts, each fanning out to `Contact.get`. Under `rbt dev run` the first push took over two minutes: the log shows every nested inline reader re-run to validate effects (`Re-running block with idempotency alias 'inline reader of 'crm.v1.Contact'...'`), so cost multiplies at each level, and other subscriptions on the page (`Pipeline.touches`, `Leads.summaries`) were starved until it finished. Same shape for the People page (`Pipeline.contacts` -> `Account.contacts` -> `Contact.get`). Workaround: keep copies of the contact facts on the account (`seat_names`, `contact_names`, `researched_contact_ids`), written by the methods that change them, so subscribed readers read one level; both slow readers dropped to about three seconds.

**Expected.** Framework fix proposed: do not re-run nested inline readers when validating an outer reader. Skill fix proposed: `servicer-reader.md` states the depth rule (a subscribed reader should be one fan-out deep) and `state-actor-decomposition.md` teaches denormalising onto the parent as a design pattern.

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-reader.md`, `python/references/state-actor-decomposition.md`.

**Checked at 1.6.0.** Neither file states a fan-out depth rule or the denormalise-onto-parent pattern (grep for `fan-out`, `denormal`, `copies`).
