---
id: returns-desk-12
project: returns-desk
source: "v 1.4.1 Reboot/Archive/returns-desk/docs/reboot-learnings.md §6"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [frontend, negative-space]
cluster: "4.2"
duplicate_of: theater-network-09
still_applies: yes
status: Open
resolved_by: ""
---

# The generated _rbt_web.ts was avoided with 8 state types in one API file (unverified)

**What happened.** The app never imports the generated web module, based on theater-network's finding that 5+ state types in one API file emit duplicate `_Reactively`/`_Idempotently` top-level symbols that esbuild rejects. With only the pb and `_rbt_react` imports, the `reboot_web.httpCall` mirror works, and `tsc -b && vite build` is green with 8 state types, as long as `_rbt_web.ts` stays unimported. The source marks this "avoided, unverified".

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/react-generated-client.md` (not named by the source).

**Checked at 1.6.0.** grep for `rbt_web` across `skills/` finds nothing; 1.6.0 projects still generate `*_rbt_web.ts`. Same gap as theater-network-09 (d).
