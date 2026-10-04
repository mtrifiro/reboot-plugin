---
id: reboot-crm-02
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P0.2"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/rpc-calls.md
tags: [auth, negative-space, pattern]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# context.auth is None in any servicer-to-servicer call, silently dropping audit entries

**What happened.** `Chat.approve` is a transaction a signed-in teammate calls to accept a change the assistant proposed; it calls `Account.set_next_step`, which records the edit in the account's own trail stamping the caller from `context.auth`. The inner call arrives app-internal with no session, so the trail's "no caller, no entry" rule dropped it and an approved change left no trace at all (not a blank-name entry; no entry). Verified: the same `set_next_step` called directly by the same teammate in the same harness records an entry with the caller's id; only the nested path loses it. Workaround: a separate INTERNAL-only method that takes the actor's id and name as request fields, called by the authenticated method that had the session.

**Expected.** Either the caller's identity propagates through a nested call, or `rpc-calls.md` says plainly it does not and that anything depending on it must pass the identity in the request. Fix options in the source: (1) runtime adds `context.caller`/`context.originator` that survives the hop; (2) reading `context.auth` inside an app-internal call raises a named error; (3) skill states identity does not cross a servicer-to-servicer call and carries the request-field workaround as a named pattern. Source recommends (3) today, then (1).

**Repro.** Nested transaction call chain as described: a teammate-called transaction calls another actor's writer that stamps the caller from `context.auth`.

**Where in the skills.** `python/references/rpc-calls.md`.

**Checked at 1.6.0.** `python/references/rpc-calls.md` has no mention of `context.auth` or identity across nested calls (grep for `auth` found nothing).
