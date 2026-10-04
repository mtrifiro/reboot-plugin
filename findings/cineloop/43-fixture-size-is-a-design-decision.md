---
id: cineloop-43
project: cineloop
source: "cineloop/reboot-findings.md §33 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/testing-project-setup.md
  - python/references/testing-harness.md
tags: [testing, cost, seeding]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# Fixture size is a design decision, and it compounds (7m50s to 3m52s)

**What happened.** The suite reached 7m50s for 33 tests, mostly one fixture: every chain-level test ran the production `initialize`, seeding 12 theaters, 48 showings and 9,600 seat records, about thirty seconds per test before any assertion. Fixes, in order of leverage: (1) parameterise the seed rather than forking it (`seed_chain(context, *, theaters, row_labels, seats_per_row)` came out of `initialize`, which calls it with the real schedule; tests call the same function with two theaters of fifty-seat houses); (2) assert against seed constants (`LAB_SHOWINGS`) rather than literals (48); (3) keep only tests that need real numbers on the real chain and merge them (three full-chain tests became one). Result 7m50s to 3m52s for the same coverage (33 tests to 32). The source predicted two minutes and was wrong by nearly 2x; a `--durations` run on one trivial test per fixture (5.0s on the big chain vs 2.2s on the small) would have given the right estimate in thirty seconds. Floor: each test boots and tears down a full Reboot runtime at about 2s even with nothing seeded (about 1 minute at 32 tests); dev-mode effect validation re-runs every writer/transaction body so mutation-heavy tests pay roughly double (a feature, not worth disabling).

**Expected.** Add to `testing-project-setup.md` 'Size the fixture to the assertion': structure the app's seeding as a function with size as a parameter, call it from `initialize` with production values and let tests call it with a fraction; reserve full-size fixtures for tests whose assertion is the production size and consider merging them.

**Repro.** Chain-level tests running the full production `initialize` (9,600 seats).

**Where in the skills.** `python/references/testing-project-setup.md`.

**Checked at 1.6.0.** `python/references/testing-project-setup.md` covers layout and fixtures-as-sharing only; no fixture-cost or parameterised-seed guidance. `testing-failure-recovery.md:168` mentions turning validation off for one test, which the source advises against generally.
