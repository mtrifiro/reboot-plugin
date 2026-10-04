---
id: reboot-air-150-03
project: reboot-air-150
source: "reboot-air/reboot-findings.md §3"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/testing-harness.md
  - python/references/lifecycle-initialize-hook.md
tags: [testing, seeding, negative-space, error-text]
cluster: "4.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# A failing initialize hook hangs rbt.up() / the test suite forever

**What happened.** When `initialize` raised (see reboot-air-02), the runtime logged `initialize for application '...' failed with ...; will retry after backoff ...` every ~10 s and `Reboot().up(...)` never returned, so `pytest` sat for the full 10-minute timeout with no failure.

**Expected.** The test harness should surface an `initialize` failure as a test error (or at least a bounded number of retries under `Reboot()`), and the `testing-*` references should mention that a hanging `up()` usually means `initialize` is failing; the traceback is only in the log noise, not in the test failure.

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-*.md` references; `python/references/lifecycle-initialize-hook.md`.

**Checked at 1.6.0.** No text under `python/references/` mentions a hanging `up()` or initialize retry-with-backoff (grep of `lifecycle-initialize-hook.md`). Framework behaviour itself not re-tested.
