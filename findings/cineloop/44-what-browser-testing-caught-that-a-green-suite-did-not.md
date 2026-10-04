---
id: cineloop-44
project: cineloop
source: "cineloop/reboot-findings.md §22 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/SKILL.md
  - app/SKILL.md
tags: [testing, frontend, pattern]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# What browser testing caught that a green suite did not

**What happened.** Table of problems found only in the browser: 60 subscriptions took 15s to render (every call correct and fast in isolation); `my_held_seats` always 0 via the fan-out (only caught if a test crossed the actor boundary); the `allowed_origins` production gap (a startup warning, not a test failure); '1 SCREENS' and film titles rendering link-blue; a blank page on `localhost` due to port collision (seen and dismissed). The instructive one: tests existed for `Showing.summary` and for `Theater.marquee` counts, but none asserted a per-caller value through the fan-out; that test now exists and fails without the fix. It is an argument for the last step of the build flow rather than a Reboot fact.

**Expected.** Source rule: test the identity-dependent field specifically at every hop it crosses; shared state survives an actor boundary, the caller does not.

**Repro.** Not recorded beyond the table.

**Where in the skills.** Last step of the build flow (`web-app/SKILL.md`, `app/SKILL.md`); related to items 28-31.

**Checked at 1.6.0.** Not located: I did not find an explicit browser-verification step in `web-app/SKILL.md` or `app/SKILL.md` by grep, but the web-app skill's later steps were not read in full, so judged unknown.
