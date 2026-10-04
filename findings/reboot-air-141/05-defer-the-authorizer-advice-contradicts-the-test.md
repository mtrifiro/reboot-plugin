---
id: reboot-air-141-05
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §5"
reboot_version: 1.4.1
severity: red
target: plugin
names:
  - web-app/SKILL.md
  - python/references/servicer-authorizer.md
  - python/references/testing-harness.md
tags: [contradiction, auth, testing]
cluster: "4.2"
duplicate_of: theater-chain-04
still_applies: yes
status: Open
resolved_by: ""
---

# Defer-the-authorizer advice contradicts the test step

**What happened.** `web-app/SKILL.md` ("Auth in Web Apps", step 1) says to omit `authorizer()` early in development; `rbt dev` allows the calls and logs a 60-second warning that serves as the TODO list, with real rules deferred until before `rbt serve` / Reboot Cloud. But build-flow step 12 (write and run backend tests before running the app for the user) boots the `Reboot()` harness, which runs production-mode authorization. The first test failed with `Airline.FleetAborted: aborted with 'PermissionDenied': You are not authorized to call 'airline.v1.AirlineMethods.Fleet'`. The deferral is not available to anyone following the build flow in order. Cost: a wasted test-suite run and a detour reading three auth references; the error invites `allow()` on every servicer, which `auth-allow-deny.md` warns against.

**Expected.** Two small edits: (1) note in "Auth in Web Apps" step 1 that the harness runs production-mode authorization so real rules are needed by build-flow step 12; (2) move authorizers from an unnumbered aside into an explicit step between the servicer (5) and the tests (12). Also add a fourth row for the `Reboot()` test harness to the `servicer-authorizer.md` mode table.

**Repro.** Not recorded.

**Where in the skills.** `web-app/SKILL.md` ("Auth in Web Apps" step 1) and `python/references/servicer-authorizer.md` versus `python/references/testing-harness.md`.

**Checked at 1.6.0.** `web-app/SKILL.md:103-111` still says "Omit `authorizer()` on Servicers" in early development. `python/references/servicer-authorizer.md:60-66` now says write `authorizer()` up front for any `oauth=` app, so the two files still disagree. The mode table (lines 40-46) has no test-harness row.
