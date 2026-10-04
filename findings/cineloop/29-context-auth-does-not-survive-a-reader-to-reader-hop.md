---
id: cineloop-29
project: cineloop
source: "cineloop/reboot-findings.md §20 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-reader.md
  - python/references/servicer-authorizer.md
  - python/references/auth-built-in-predicates.md
tags: [negative-space, auth]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# context.auth does NOT survive a reader-calling-a-reader hop

**What happened.** `Showing.summary` returns `my_held_seats` computed from `context.auth.user_id`. Called by the browser it works. Called from `Theater.marquee`'s fan-out, `context.auth` is `None`: the inner call arrives app-internal with no identity even though the outer call was authenticated as a real patron. Symptom is quietly wrong data, not an error: the lobby showed correct `held_seats` and `my_held_seats: 0`; nothing failed, the badge never appeared. The source's fix threads the viewer explicitly: a `_viewer(context, claimed_id)` helper that returns the real caller if `context.auth` is set (ignoring the claim), returns `claimed_id` only when there is no token AND `context.app_internal`, else empty. Safe because an external caller always has auth so their claim is ignored; a test covers that. The source calls this the sharpest thing learned, costing real debugging time and 'in none of the references'.

**Expected.** Add to `servicer-reader.md` under 'Calling Other Actors Is Allowed (But Read-Only)': identity does not propagate. A reader calling another actor's reader makes the inner call app-internal, `context.auth` is `None` inside it, and anything derived from `context.auth` (a `mine` flag, per-user count, owner check) silently computes as if nobody is signed in. If an inner reader needs the caller pass the ID explicitly and guard it (use `request.viewer_id` only when `context.auth` is absent and `context.app_internal`). The same applies to `is_app_internal` in the inner actor's authorizer: a user-only rule denies the fan-out.

**Repro.** Fan-out reader calling an inner reader that reads `context.auth`.

**Where in the skills.** `python/references/servicer-reader.md` section 'Calling Other Actors Is Allowed (But Read-Only)'.

**Checked at 1.6.0.** `python/references/servicer-reader.md` lines 63-65 say the call 'propagates the `ReaderContext`', which can read as identity propagating; no statement that `context.auth` is None on the inner call. The same file does not mention `is_app_internal` for fan-out.
