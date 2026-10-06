---
id: returns-desk-04
project: returns-desk
source: "v 1.4.1 Reboot/Archive/returns-desk/docs/reboot-learnings.md §5"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [frontend, negative-space]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# One-shot httpCall users meet protobuf-es classes that wrap repeated fields, and nothing documents them

**What happened.** For the one-shot `httpCall` path (needed because reactive fan-out readers deliver no first frame, as theater-network found), the pb response wraps a `list[Model]` field as `response.invariants?.items`, while the generated React hooks expose the same field as a plain camelCase array; every pb getter is also `string | undefined`. Cost one type-check cycle. `react-generated-client.md` documents the Zod side; nothing documents the pb side that `httpCall` users must touch.

**Expected.** Not recorded beyond the gap: the pb response shape (repeated fields under `.items`, optional getters) documented for `httpCall` users.

**Repro.** Not recorded.

**Where in the skills.** `python/references/react-generated-client.md`.

**Checked at 1.6.0.** grep for `httpCall`, `protobuf-es`, `_pb` and `rbt_web` across `skills/` finds nothing relevant; `react-generated-client.md` mentions only `*_rbt_react.ts` and Zod-validated types. The surface still exists: 1.6.0 projects (reboot-crm, client-portal) generate `*_pb.ts` and `*_rbt_web.ts`.
