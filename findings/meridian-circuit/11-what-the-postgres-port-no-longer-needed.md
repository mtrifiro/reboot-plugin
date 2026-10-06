---
id: meridian-circuit-11
project: meridian-circuit
source: "v 1.4.1 Reboot/meridian-circuit/docs/2026.08.18 reboot-learnings porting supabase app.md §Notes on the port itself"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/scheduling-basic.md
  - python/references/servicer-transaction.md
  - python/references/api-errors.md
tags: [pattern]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# What the Supabase/Postgres version needed that disappears in Reboot

**What happened.** Port notes: (1) `release_expired_holds()` and its sweep are gone: a hold's expiry is a durable timer on the showing actor that fires on its own and survives a restart. (2) The polling fallback is gone: the original ran a realtime subscription plus a 5s poll because an expiring hold writes no row and pushes no change event; here the expiry is a write, so the subscription alone is complete. (3) `SELECT … FOR UPDATE` in checkout became a transaction across the cart's seats: if any hold has lapsed the whole order rolls back, including seats already sold earlier in the same call. (4) `'taken'` / `'limit'` string returns became typed errors (`SeatUnavailableError`, `CartFullError`) that the UI turns into specific sentences. (5) The browser-driven crowd (`setInterval` calling a `simulate_crowd()` SQL function) became a server-side actor, so maps move whether or not a tab is open and the switch is shared across viewers.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** No porting guide exists; the individual mechanisms live in `scheduling-basic.md`, `servicer-transaction.md` and `api-errors.md`.

**Checked at 1.6.0.** The mechanisms are documented individually (scheduled writers for expiry in `scheduling-basic.md` § Never, rollback in `servicer-transaction.md`, typed errors in `api-errors.md`), but no skill frames them as a port from a SQL/realtime backend (grep for `Postgres`/`Supabase`/`FOR UPDATE` found nothing).
