---
id: theater-chain-11
project: theater-chain
source: "theater-chain/reboot-findings.md §11"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [pattern, cost, frontend]
cluster: "D"
still_applies: yes
status: Resolved
resolved_by: "python/references/react-generated-client.md § Scales as; python/references/patterns-load-and-benchmarking.md § Scales as"
---

# Reactive readers are per-response so split fat readers

**What happened.** The dashboard shows all 48 showings at once. Subscribing each to `Showing.get` would stream 48 x 200 seat records on every change anywhere in the chain; `Showing.stats` returns eight integers instead and only the seat-map page subscribes to the full map. Measured: 48 simultaneous reader subscriptions come up fine but fill in progressively over roughly ten seconds, so components need a per-subscription loading state; a single page-level spinner would sit through the whole ramp.

**Expected.** `react-generated-client.md` says "Live Updates Are Free" - true per subscription; add a sentence on what "free" costs when a page mounts dozens, plus the summary-reader pattern.

**Repro.** Not recorded.

**Where in the skills.** `python/references/react-generated-client.md`, "Live Updates Are Free".

**Checked at 1.6.0.** Still absent. `python/references/react-generated-client.md:113` still has "Live Updates Are Free" with no summary-reader or many-subscription cost note (grep for summary / subscriptions found nothing).
