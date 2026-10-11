---
id: crm-kit-34
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §5"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/patterns-cross-actor-reads.md
tags: [cost, pattern]
cluster: "D"
duplicate_of: reboot-crm-31
still_applies: no
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this"
---

# Keep a subscribed reader one fan-out deep; denormalise child facts onto the parent

**What happened.** Effect validation re-runs every nested inline reader, so the cost multiplies at each level. A two-level fan-out over about 100 actors took over 2 minutes to first push and starved the page's other subscriptions; denormalised, about 3 s. About 3 s to first push over about 50 actors is normal in dev, and later pushes are incremental, so do not optimise it. When something looks stuck, check `rbt task list`: the app log lags by minutes under load.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/patterns-cross-actor-reads.md` § Do this, per the canonical item reboot-crm-31. `rbt task list` and the log lag are not mentioned under `skills/` (grep).
