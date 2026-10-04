---
id: showtime-22
project: showtime
source: "2026.08.18 reboot-findings.md #22"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [pattern, frontend]
cluster: "E"
still_applies: yes
status: Open
resolved_by: ""
---

# Pair reactive readers with optimistic overrides

**What happened.** A cross-actor transaction (plus dev-mode effect-validation re-runs) takes a perceptible beat. Paint the expected state locally on click and let the pushed reader update confirm it. Reconciliation is trivial because readers are push-based: drop each override as soon as the server snapshot matches, revert it if the mutation resolves `aborted`. No refetch orchestration.

**Expected.** See suggested improvement 5: `react-generated-client.md` could sketch the ~20-line pattern.

**Repro.** Not recorded.

**Where in the skills.** `react-generated-client.md` documents 'live updates are free' but not this companion idiom.

**Checked at 1.6.0.** python/references/react-generated-client.md:112-116 ('Live Updates Are Free') has no optimistic-override pattern; grep for `optimistic` across skills returns nothing.
