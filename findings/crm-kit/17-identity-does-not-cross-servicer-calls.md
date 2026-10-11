---
id: crm-kit-17
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §3"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/servicer-authorizer.md
  - python/references/rpc-calls.md
  - python/references/rpc-constructor-calls.md
tags: [auth, negative-space]
cluster: "4.1"
duplicate_of: cineloop-29
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-authorizer.md § Never"
---

# context.auth is None in every servicer-to-servicer call; pass identity as request fields

**What happened.** `context.auth` is `None` in every nested call, including a factory `create` reached from another actor's transaction. An "only record if we know the caller" rule then drops the audit row entirely. Fix: the outer, authenticated method reads `context.auth` and passes `by_id` and `by_name` to an `INTERNAL`-only method; anything a constructor stamps (owner, first history entry) is passed the same way.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `rpc-calls.md` and `rpc-constructor-calls.md` are silent on nested calls losing identity (§11).

**Checked at 1.6.0.** `python/references/servicer-authorizer.md` § Never states `context.auth` is `None` in any call from inside a servicer and to pass the user id as a request field.
