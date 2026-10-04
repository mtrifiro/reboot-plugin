---
id: cineloop-11
project: cineloop
source: "cineloop/reboot-findings.md §11 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - web-app/references/react-client.md
  - python/references/react-generated-client.md
tags: [pattern, frontend]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Reactive hooks and rules-of-hooks: one reactive hook per component

**What happened.** The lobby needs one live subscription per showing. `useShowing(id)` inside a `.map()` over an array that starts empty and becomes 48 entries violates the rules of hooks (hook count changes between renders). Fix: one reactive hook per component; when N live subscriptions are needed render N components, each owning one (`<ShowingCard id={id} />` calls exactly one `useShowing`; the parent maps over IDs and renders components, never hooks).

**Expected.** Not recorded.

**Repro.** `useShowing(id)` inside `.map()` over a list that changes length.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E). The plugin gap is item 17.
