---
id: meridian-circuit-01
project: meridian-circuit
source: "v 1.4.1 Reboot/meridian-circuit/docs/2026.08.18 reboot-learnings porting supabase app.md §1"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/patterns-cross-actor-reads.md
  - python/references/patterns-load-and-benchmarking.md
  - python/references/scheduling-recurring.md
tags: [cost, pattern]
cluster: ""
duplicate_of: theater-network-08
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this"
---

# A reader that fans out is the wrong shape for a dashboard aggregate (48 actors: 8 s, or a 503)

**What happened.** Porting a Lovable/Supabase seat-reservation app. The dashboard needs sold / held / open for all 48 showings; the obvious `Chain.stats` Reader calls every `Showing.stats` and sums. Measured on a warm backend: one `Showing.stats` from outside 45ms; 12 in parallel from outside 727ms; `Chain.stats` fanning out to 48 in waves of 12 8.0s, waves of 24 8.3s, all at once 115s (first call). A nested cross-actor read costs roughly 170ms, about 4x an external one, and raising concurrency makes it dramatically worse. The browser saw a 503 `Unavailable: ping timeout` and a dashboard of zeroes. The author's fix: cache the aggregate on the actor and rebuild it from a background loop, so `Chain.stats` returns a stored snapshot (8s to 70ms, paid once per cycle however many dashboards are open). The loop is three methods: `start_stats` (Writer, guarded by a `stats_refreshing` flag so a second call never starts a second loop; schedules the workflow); `refresh_stats` (Workflow, does the fan-out with every call scoped `.per_workflow(...)`, then calls `store_stats`); `store_stats` (Writer, saves the snapshot and schedules the next `refresh_stats`; extending the chain from here rather than the workflow means exactly one refresh is ever in flight).

**Expected.** Rule of thumb from the source: if a read fans out to more than a handful of actors, cache it; waves of about 12 are the sweet spot when you must fan out.

**Repro.** `Chain.stats` reader fanning out to 48 `Showing.stats` calls (timings above).

**Where in the skills.** `patterns-cross-actor-reads.md` (step 4 recommends a fan-out reader on the parent and reserves materialize-on-write for about 150 children); `patterns-load-and-benchmarking.md`. Same gap as theater-network-08 (fan-out readers have a request budget); compare reboot-visualization-01 (48 seats, same symptom). The source does not establish whether reboot-crm-07's post-restart Envoy window contributed.

**Checked at 1.6.0.** `patterns-cross-actor-reads.md` § Do this step 4 still recommends `Showing.forall(...).summary(context)` one level deep and materializing only for 'very wide fan-out (about 150 children)'; § Limits and `patterns-load-and-benchmarking.md` § Limits cite only the 150-actor failure. Grep for `cache`/`snapshot` in those files and `scheduling-recurring.md` found no cached-aggregate loop, and nothing records the nested-read cost or a failure at 48.
