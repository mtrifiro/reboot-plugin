---
id: ticketing-05
project: ticketing
source: "Punch List - Ticketing App Build Findings.md §5"
reboot_version: 1.4.1
severity: unrated
target: primer
names: []
tags: [auth, cost, pattern]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Chapter 7: two review-checklist items the build hit

**What happened.** (a) Authorizers vs scheduled work: a workflow scheduled by a writer/transaction runs app-internally with no bearer token, so an actor whose authorizer only accepts user identity denies its own scheduled workflow. Rule that worked: `allow_if(any=[<user rule>, is_app_internal])` on any actor with self-scheduled work. (b) Subscription shape is a builder decision: reader hooks are push-based and the framework supports one subscription per instance, which is usually wrong for a collection view; one reader per business question ('the seat map'), not one per instance.

**Expected.** Reviewers should look for both.

**Repro.** Not recorded.

**Where in the skills.** Primer Chapter 7 - What the Framework Leaves to You.
