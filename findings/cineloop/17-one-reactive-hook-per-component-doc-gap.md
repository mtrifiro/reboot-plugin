---
id: cineloop-17
project: cineloop
source: "cineloop/reboot-findings.md Part 2 §D"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/references/react-client.md
  - python/references/react-generated-client.md
tags: [negative-space, frontend, pattern]
cluster: "E"
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-react-state.md § Never"
---

# Add 'one reactive hook per component' to react-client.md

**What happened.** N live subscriptions over a dynamic list is the common shape for any dashboard and collides head-on with React's rules of hooks. Nothing in the skill mentions it. (See item 11.)

**Expected.** Add: use<Type>(id) cannot be called inside a `.map()` over a list that changes length; render a child component per item and let each own exactly one subscription (`ids.map(id => <ShowingCard key={id} id={id} />)` correct; `ids.map(id => useShowing(id))` wrong). Also what makes per-item re-render granularity work.

**Repro.** Not recorded.

**Where in the skills.** `web-app/references/react-client.md`; also `mcp-ui` react references for builder parity.

**Checked at 1.6.0.** No mention of rules-of-hooks / hook-in-map anywhere under `skills/` (grep found nothing).
