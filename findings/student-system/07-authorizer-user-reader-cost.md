---
id: student-system-07
project: student-system
source: "student-system/reboot-findings.md §7"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/servicer-authorizer.md
  - python/references/auth-custom-predicates.md
tags: [cost, auth, negative-space]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# Every authorizer decision costs a reader call to User

**What happened.** Roles live on the `User` actor and the authorizer predicate reads `User.ref(user_id).profile(context)` on every call to every other type, readers included. That doubles round trips for a page load and explains most of the 43 Reboot calls the dashboard's analysis found between nine servicers.

**Expected.** Guidance in the auth references on where role claims should live (token claims via the OAuth provider? a cached lookup?) and whether a reader call from inside an authorizer predicate has any cost beyond the round trip.

**Repro.** Not recorded.

**Where in the skills.** Auth references (`servicer-authorizer.md`, `auth-custom-predicates.md`).

**Checked at 1.6.0.** No text in `python/references/servicer-authorizer.md` or `auth-custom-predicates.md` discusses where role claims should live or the cost of reading `User` in a predicate (grep for `claims` in the auth references found nothing).
