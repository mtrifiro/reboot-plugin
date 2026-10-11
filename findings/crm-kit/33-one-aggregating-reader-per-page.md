---
id: crm-kit-33
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §5"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/patterns-cross-actor-reads.md
  - python/references/servicer-reader.md
  - python/references/react-generated-client.md
tags: [cost, negative-space]
cluster: "D"
duplicate_of: reboot-crm-30
still_applies: no
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this"
---

# Give each page one aggregating reader, not a subscription per actor; subscribed readers are transitively reactive

**What happened.** A reader re-runs when any state it read through other actors' readers changes, `forall` included. The references never said so, and one page had 141 WebSocket streams. §11: `servicer-reader.md` and `react-generated-client.md` are silent on transitive reactivity.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `servicer-reader.md`, `react-generated-client.md` (§11).

**Checked at 1.6.0.** `python/references/patterns-cross-actor-reads.md` § Do this, per the canonical item reboot-crm-30.
