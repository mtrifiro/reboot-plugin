---
id: cineloop-20
project: cineloop
source: "cineloop/reboot-findings.md Part 2 §G"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/SKILL.md
tags: [negative-space, pattern, frontend]
cluster: "4.2"
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this"
---

# The web-app skill should mention the summary-vs-detail reader split

**What happened.** The skill's build flow goes API, servicer, frontend, and the reader-granularity problem only appears once a list view over many actors is built. By then the API is written and adding `summary` means another `rbt generate` round trip.

**Expected.** Add to the State Model Assessment (step 6, 'Pages / routes'): for each page ask what it needs per actor. A list or dashboard page over N actors usually wants a cheap summary reader (counts, status, a title) while the detail page wants the full payload; declare both up front, because with reactive readers a list page subscribes to all N actors at once and an over-broad reader multiplies payload and re-render cost by N. (See item 10.)

**Repro.** Not recorded.

**Where in the skills.** `web-app/SKILL.md` State Model Assessment; likely the shared build spine (proposal 4.2).

**Checked at 1.6.0.** `web-app/SKILL.md` has no summary/detail reader guidance (grep for 'summary reader' found nothing in `web-app/` or `mcp-ui/`).
