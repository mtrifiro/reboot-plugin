---
id: reboot-air-141-17
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §17"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/auth-built-in-predicates.md
  - python/references/servicer-reader.md
  - python/references/servicer-transaction.md
tags: [negative-space, auth, error-text]
cluster: "4.1"
duplicate_of: cineloop-29
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-authorizer.md § Never"
---

# Servicer-to-servicer call drops caller identity and no reference says so

**What happened.** While gating `Flight.take_seats` on `is_app_internal`, the author needed to know whether an in-app servicer-to-servicer call arrives app-internal or carries the original caller's identity. No reference answers it. `auth-built-in-predicates.md` says `is_app_internal` returns `Ok` when the call originates from inside the same app, and a note on self-scheduled workflows says a scheduled workflow "has no bearer token, even when the original transaction was authenticated", framed as special to scheduling. The truth, established by a 3.5-minute targeted test run: an in-app call is app-internal AND has no `context.auth` at all. A reader gated on `has_verified_token` alone fails when another servicer fans out to it: `Flight.DetailsAborted: aborted with 'Unauthenticated': You are not authorized to call 'airline.v1.FlightMethods.Details'`. This decides whether any composing reader works (the chat-app skill recommends composing readers), and makes the `is_app_internal` arm of `allow_if(any=[has_verified_token, is_app_internal])` load-bearing rather than belt-and-braces.

**Expected.** State once, prominently, in `auth-built-in-predicates.md`: a call from one Servicer to another arrives app-internal with no bearer token; the caller's `user_id` is not propagated; any type reachable from a composing reader or cross-actor transaction needs `is_app_internal`. Cross-link from `servicer-reader.md`'s "Calling Other Actors Is Allowed" section.

**Repro.** Not recorded.

**Where in the skills.** `python/references/auth-built-in-predicates.md`, `servicer-reader.md`, `servicer-transaction.md`.

**Checked at 1.6.0.** Still absent. `python/references/auth-built-in-predicates.md:38-48` still describes `is_app_internal` only as "another Servicer calling this one" and lines 92-119 cover only self-scheduled workflows; no statement that in-app calls carry no `context.auth`.
