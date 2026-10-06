---
id: crm-kit-55
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §8"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - web-app/references/react-client.md
tags: [frontend, scaffold, negative-space]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# tsc --noEmit checks zero files under the Vite references tsconfig; type-check with npx tsc -b

**What happened.** The Vite `tsconfig.json` is a references stub (`"files": []`), so `tsc --noEmit` checks zero files and exits 0. A call to a deleted `use<Method>` hook reached `main` that way. Rule: `cd web && npx tsc -b`, after every API rename or delete.

**Expected.** Type-check with `npx tsc -b`, never `tsc --noEmit`.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source.

**Checked at 1.6.0.** `build/templates/README.md` says the web `build` script is `tsc -b && vite build`, but no reference warns that `tsc --noEmit` checks nothing with project references or says to run `tsc -b` after an API rename (grep `noEmit`).
