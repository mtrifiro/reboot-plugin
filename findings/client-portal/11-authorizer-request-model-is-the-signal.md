---
id: client-portal-11
project: client-portal
source: "client-portal/reboot-findings.md §11"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/auth-custom-predicates.md
  - python/references/servicer-authorizer.md
tags: [auth, negative-space]
cluster: "4.1"
still_applies: unknown
status: Open
resolved_by: ""
---

# Authorizers: the request model is the signal (fail closed, request=None lands on the member path)

**What happened.** One rule governs a whole servicer, so `servicers/authorizers.py` tells a member's read from administration by which request model arrived, and fails closed on anything it does not recognise. Adding a method with a request model therefore makes it staff-or-internal by default, and adding one with `request=None` puts it on the member-facing path. The author calls this a good default (a method added later is unreachable from outside until someone names it) but it means "why is this refused?" usually answers itself at the request model, not in the predicate. A related trap, the author's own: `Document.get` returned `PermissionDenied` for every note because `document_for_path` handed back the index's whole JSON row instead of the `id` inside it, and `document_access` fails closed when `state is None`; permission-denied was the symptom, a malformed id the cause.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/auth-custom-predicates.md` (request-type dispatch).

**Checked at 1.6.0.** `auth-custom-predicates.md` (line ~136) shows `isinstance(request, ...)` dispatch but not the fail-closed default or the `request=None` consequence (see student-system-06).
