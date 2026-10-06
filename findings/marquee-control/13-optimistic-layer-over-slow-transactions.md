---
id: marquee-control-13
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 13"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/patterns-react-state.md
tags: [frontend, pattern]
cluster: ""
duplicate_of: showtime-22
still_applies: no
status: Resolved
resolved_by: "python/references/patterns-react-state.md § Optimistic overrides"
---

# Sub-100ms UI on top of 0.5-3 s transactions: an optimistic layer reconciled by the reactive push

**What happened.** A cart `add_seat` transaction takes about 0.5-3 s in dev (2PC plus effect validation), so the UI paints first and reconciles after: click gives a synthesized cart entry with an `opt:`-prefixed holdId and the seat painted 'yours (confirming)' (measured 32 ms click-to-paint); the server's pushed cart state replaces the optimistic entry when the real hold lands; an abort reverts the paint and shows the typed error; a 10 s confirm deadline sweeps anything the server never answered (theater-network's pattern). Releases hide the entry and repaint the seat immediately (21 ms) and let the push settle it. Optimistic entries refuse removal until confirmed (no real holdId to release yet); that is the one interaction the pattern must gate.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `patterns-react-state.md`. Same pattern as showtime-22.

**Checked at 1.6.0.** `patterns-react-state.md` § Optimistic overrides teaches paint-then-reconcile with revert on `aborted`, and says to disable irreversible actions while an override is unconfirmed; § A deadline on every mutation in a dev-loop UI covers the sweep.
