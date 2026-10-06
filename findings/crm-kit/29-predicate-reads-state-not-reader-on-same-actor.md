---
id: crm-kit-29
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §4"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/auth-custom-predicates.md
tags: [auth, negative-space]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# In a predicate on type X, read the state argument; calling a reader on the same actor makes it wait on itself

**What happened.** Authorizing a call on an actor while asking that same actor (a reader call from the predicate) makes the actor wait on itself.

**Expected.** Read the `state` argument in the predicate; never call a reader on the same actor.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source.

**Checked at 1.6.0.** `servicer-authorizer.md` § Limits says the authorizer runs with the actor's `state`; `auth-allow-if.md` § Scales as notes the cost of predicates that read another actor. Nothing warns against a reader call on the same actor from its own predicate (grep `itself`, `same actor`, `deadlock` in the auth references).
