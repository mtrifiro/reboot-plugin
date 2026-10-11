---
id: encore-03
project: encore
source: "v 1.4.1 Reboot/encore/docs/reboot-learnings 02.md §3"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/patterns-error-handling.md
tags: [negative-space]
cluster: "4.1"
duplicate_of: theater-chain-05
still_applies: no
status: Resolved
resolved_by: "python/references/patterns-error-handling.md § Carrying a typed error across an actor boundary"
---

# Typed errors do not tunnel through transactions intact

**What happened.** Letting a participant writer's typed abort (`Seat.HoldAborted` carrying `SeatUnavailableError`) propagate raw out of a transaction delivers the method-union wrapper (`SeatHoldErrors {...}`) to the caller, not the declared error: `isinstance(aborted.error, SeatUnavailableError)` is False at the call site even though both methods declare the error. Fix: catch the participant's abort inside the transaction and re-raise it as the transaction's own declared error (`except Seat.HoldAborted as aborted: if isinstance(aborted.error, SeatUnavailableError): raise Cart.HoldSeatAborted(aborted.error) from None; raise`). The author notes theater-network's cart does the same, "now we know why".

**Expected.** Not recorded.

**Repro.** A `Cart` transaction calling `Seat.hold`, both declaring `SeatUnavailableError`, with no catch in the transaction.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/patterns-error-handling.md` § Carrying a typed error across an actor boundary gives the explicit re-raise recipe and says the payload arrived empty at 1.4.1 (intact with the 1.6.0 template when both declare the same class).
