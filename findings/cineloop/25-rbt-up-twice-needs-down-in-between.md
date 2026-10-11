---
id: cineloop-25
project: cineloop
source: "cineloop/reboot-findings.md §16 (Part 3)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/testing-failure-recovery.md
  - python/references/testing-harness.md
tags: [testing, error-text]
cluster: "4.4"
still_applies: no
status: Obsolete
resolved_by: ""
---

# rbt.up() twice needs down() in between

**What happened.** Testing that `initialize` is safe to re-run (important here: a re-seed would wipe an auditorium patrons are looking at) means restarting the app under test. Calling `rbt.up()` a second time raises `ValueError: This application is already up`. The fix is `await self.rbt.down()` first, and then to mint fresh contexts, since the old ones are bound to the torn-down application.

**Expected.** Add to `testing-failure-recovery.md` / `testing-harness.md` a 'Restarting the application under test' note: `await self.rbt.down()`, `await self.rbt.up(Application(...))`, then create a fresh context; `up()` on an already-up app raises `ValueError: This application is already up`, and contexts created before the restart are bound to the old one.

**Repro.** Call `rbt.up()` twice without `down()`.

**Where in the skills.** `python/references/testing-failure-recovery.md`, `testing-harness.md`.

**Checked at 1.6.0.** `python/references/testing-failure-recovery.md` lines 36-53 now state 'down() before a second up()' with the `ValueError("This application is already up; ...")` text. The 'old contexts are bound to the torn-down app' point was not found.
