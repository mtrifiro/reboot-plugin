---
id: theater-chain-20
project: theater-chain
source: "theater-chain/reboot-findings.md §18"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/testing-harness.md
  - python/references/testing-failure-recovery.md
tags: [cost, testing, operations]
cluster: "D"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-load-and-benchmarking.md § Do this; python/references/testing-harness.md § Scales as"
---

# Measure on a quiet machine and distrust a single sample

**What happened.** A commit message recorded "~610ms" as a regression, but over the day the same click measured 110, 610, 865, 930, 950, and 1050 ms with no code change explaining most of it. Confounders: `mds_stores` at 347% CPU with load average 10+ (moving the project into `~/projects` and rebuilding `.venv` and `node_modules` sent Spotlight to reindex tens of thousands of files); and a page that outlived its backend (after `rbt dev run` restarts an open tab keeps retrying dead subscriptions, the console fills with `Not expecting stream to ever be done`, clicks land and no push arrives). The 110 ms figure never reproduced. Rules: (1) check ambient load first (`uptime`); (2) reload the page after restarting the backend; (3) benchmark in the harness, not the browser, before and after in the same process, with `from reboot.aio.contexts import EffectValidation` and `await rbt.up(Application(servicers=[...], libraries=[...]), effect_validation=EffectValidation.DISABLED)` because production does not re-run writer bodies; this is how the 10x in §16 was measured. Controlled run (20 samples per phase, `scripts/latency-probe.sh`, page reloaded each phase): freshly restarted backend load 2.57 p50 848 ms p95 868 ms; after 12 `--watch` reloads load 3.97 p50 970 ms p95 1045 ms; restarted again load 3.15 p50 852 ms p95 862 ms. A long-lived `--watch` session degrades latency by about 14% and a restart fully recovers it (not the 5x originally guessed). Caveats: one trial per condition, not interleaved; phases ran at different load averages.

**Expected.** Document `rbt.up(..., effect_validation=EffectValidation.DISABLED)` for benchmarking in `testing-harness.md`, together with the stale-page-after-restart rule and "restart `rbt dev run` before benchmarking".

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-harness.md`.

**Checked at 1.6.0.** Partly addressed. `python/references/testing-failure-recovery.md:177-183` now uses `effect_validation=EffectValidation.DISABLED`, but `python/references/testing-harness.md` has no benchmarking guidance, and no benchmarking or stale-tab/restart rules were found in the skills.
