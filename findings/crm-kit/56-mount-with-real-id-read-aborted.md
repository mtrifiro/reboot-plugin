---
id: crm-kit-56
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §8"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [frontend]
cluster: "4.1"
duplicate_of: reboot-crm-78
still_applies: no
status: Resolved
resolved_by: "python/references/react-generated-client.md § Never"
---

# Mount an id-needing component only once the id is known, read each mutation's aborted, and type handles as Use<Type>Api

**What happened.** Hooks need a real id on every render. Mutations never throw, so an unread `aborted` swallows the error. `ReturnType<typeof useFoo>` resolves to the no-argument overload; type handles as `Use<Type>Api`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/react-generated-client.md` § Do this (line ~111: mount the child with a real id), "Mutations resolve to `{ response, aborted }`, never throw", and § Never (line ~121) on `ReturnType<typeof useFoo>`.
