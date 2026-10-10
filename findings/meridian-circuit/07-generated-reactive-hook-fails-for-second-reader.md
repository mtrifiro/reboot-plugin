---
id: meridian-circuit-07
project: meridian-circuit
source: "v 1.4.1 Reboot/meridian-circuit/docs/2026.08.18 reboot-learnings porting supabase app.md §7"
reboot_version: 1.4.1
severity: unrated
target: framework
names:
  - python/references/react-generated-client.md
tags: [frontend, error-text]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "python/references/react-generated-client.md § Errors you will see"
---

# The generated reactive hook works for one reader and throws for another on the same type

**What happened.** `useChain(...).useGet()` works; `useChain(...).useStats()`, a second Reader on the same state type with the same `request=None` shape, throws inside the generated client: `TypeError: Cannot set properties of undefined (setting '<uuid>') at ChainInstance.useStats`. It fails at `reader.setResponses[id] = setResponse`, so the reader object returned by `startStats` lacks its listener maps. It fails the same way when `useStats()` is the only reader on the page, so it is not a two-subscriptions problem. The generated source for `startStats` and `startGet` is structurally identical, pointing at the client runtime rather than codegen. Workaround: the one-shot call (`await chain.stats()`) works; since item 1 made the read O(1) (70ms) the dashboard polls instead of subscribing. The seat map still uses a real subscription (`useShowing(...).useGet()`).

**Expected.** Not recorded. The source marks it worth reporting upstream.

**Repro.** A second `request=None` Reader on a state type, subscribed with its generated `use<Reader>()` hook.

**Where in the skills.** Runtime bug; `python/references/react-generated-client.md` has no note.

**Checked at 1.6.0.** Not checked against the 1.6.0 client runtime. Grep for `Cannot set properties`/`setResponses` across `skills/` found nothing.

**Resolution (2026-10-10).** Rows in `react-generated-client.md` § Errors you will see: the UUID idempotency key; the second reader's hook throwing (1.4.0); int64 as `number`; a subscription on an unconstructed actor tearing the channel; the six-connection ceiling. The `#`-in-id trap already had its row; the `_rbt_web.ts` import failure is proto-era (1.4.0) and not carried.
