---
id: meridian-circuit-05
project: meridian-circuit
source: "v 1.4.1 Reboot/meridian-circuit/docs/2026.08.18 reboot-learnings porting supabase app.md §5"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/rpc-refs.md
  - python/references/react-generated-client.md
tags: [negative-space, testing, frontend]
cluster: ""
duplicate_of: cineloop-33
still_applies: no
status: Resolved
resolved_by: "python/references/rpc-refs.md § Never; python/references/react-generated-client.md § Limits"
---

# A reader on a never-constructed actor aborts (the loser's Cart in a contested add)

**What happened.** In a contested `add_seat` the loser's whole transaction rolls back, so the loser's `Cart` actor is never constructed, and a later `Cart.ref(loser).get(...)` aborts with `StateNotConstructed` rather than returning zero state. Do not assert 'the loser's cart is empty'; assert the winner's cart, or catch the abort. The same trap applies to any UI that subscribes to an actor before anything has written it: touch it with a no-op write first.

**Expected.** Not recorded.

**Repro.** Two carts race for one seat; read the losing cart.

**Where in the skills.** `python/references/rpc-refs.md`; `react-generated-client.md` for the subscription case. Same gap as cineloop-33 and marquee-control-09.

**Checked at 1.6.0.** `rpc-refs.md` now says a reader on a never-constructed actor aborts `StateNotConstructed` for every type ("Does this actor exist?") and § Never forbids assuming zero state; `react-generated-client.md` § Limits says subscribing to an unconstructed actor aborts and retries: construct, then mount.
