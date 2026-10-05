---
title: Cross-Actor Reads and Reader Shape
impact: HIGH
impactDescription: Wrong actor boundaries turn one click into a distributed transaction; wrong reader shapes stream N full payloads to every list page or leak other users' data
tags: patterns, reader, reactive, fan-out, summary reader, view model, derived state, decomposition, cohesion
summary: "Run the cohesion test before splitting; derived projections, summary/detail readers, one-level server-side aggregation, per-caller views."
step: any
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Cross-Actor Reads and Reader Shape

## When you are here

Deciding inline collection vs actor per item, stored vs derived value,
or which readers a page over many actors calls. Mechanics:
`state-actor-decomposition.md`, `state-collections.md`; numbers:
`patterns-load-and-benchmarking.md`.

## Do this

### 1. Run the cohesion counter-test before splitting a collection

Decomposition signals (identity, lifecycle, own methods) say when to
split; the counter-test says when not to: **must one user action change
several items all-or-nothing?** ("hold these 4 seats", "move these 3
cards"). If yes, keep them inline on one actor.

- Inline `list[Seat]` on one `Showing`: a multi-seat hold is one writer
  body, the 8-seat cap is checked in the writer that grants it, and two
  patrons racing for F-12 are ordered, the loser getting a typed error
  (cineloop-01, 1.4.1).
- Actor per seat: the same hold is a transaction over up to 8 actors.

Group what must change together; split what must scale independently.
Splitting doesn't help if every write still touches one shared actor:
per-seat actors plus occupancy counters on the `Showing` convoyed 20
concurrent customers into
`Timed out waiting 30.0s to acquire exclusive lock`
(theater-network-01, 1.4.0). Derive bookkeeping in a reader instead.

### 2. Derive what is a projection of state you already have

Before adding a state `Type` or field, check whether it is computable.
A cart computed in the reader as "seats on this showing held by me"
can't disagree with the holds and needs no cleanup when a hold expires
(cineloop-02, 1.4.1). A wrong `Type` is expensive: persisted schemas
evolve additively only (`api-schema-evolution.md`).

**Reactive updates track mutations, not computed values:** a reader
deciding at read time that a hold lapsed changes no state, so no other
subscriber re-renders. Keep the lazy check for correctness and add a
scheduled writer that commits the transition for liveness
(cineloop-03, cineloop-16, 1.4.1; `scheduling-basic.md`).

### 3. Declare summary and detail readers together

Reader shape is a performance API: a list page over N actors wants a
cheap summary, the detail page the full payload. Declare both with the
API, before the frontend:

```python
class ShowingSummary(Model):
    available: int = Field(tag=1, default=0, description="Seats free now.")
    held: int = Field(tag=2, default=0, description="Seats held, unsold.")
    sold: int = Field(tag=3, default=0, description="Seats sold.")
    mine: int = Field(tag=4, default=0, description="Seats the caller holds.")

ShowingMethods = Methods(
    seat_map=Reader(
        request=None, response=SeatMapResponse,
        description="Every seat with its status, for the seat-map page.",
        mcp=None,
    ),
    summary=Reader(
        request=None, response=ShowingSummary,
        description="Seat counts only, for list and lobby pages.",
        mcp=None,
    ),
)
```

48 lobby cards calling `seat_map` would ship about 9,600 seat views per
frame, re-pushed on every hold; `summary` is about 2% of the payload
with the same reactivity (cineloop-10, 1.4.1; also theater-chain-11).

### 4. Aggregate on the server, one level deep

A subscribed reader is **transitively reactive**: it re-runs when any
actor it read through another actor's reader (including `forall`)
changes. Undocumented publicly; in the 1.6.0 source
(`SidecarStateManager.reactively` installs `React` "providing
transitive reactivity"), observed at 1.4.1 (showtime-27, cineloop-28)
and 1.6.0 (reboot-crm-30). Give the parent a fan-out reader and
subscribe once:

```python
async def marquee(
    self, context: ReaderContext,
) -> Theater.MarqueeResponse:
    cards = await Showing.forall(self.state.showing_ids).summary(context)
    return Theater.MarqueeResponse(cards=cards)
```

- Twelve `marquee` subscriptions replaced sixty per-showing ones
  (cineloop-28, 1.4.1).
- Keep it one fan-out deep: for a second level, copy the needed facts
  onto the parent from the methods that change them (reboot-crm-31,
  1.6.0).
- Very wide fan-out (about 150 children): materialize on write; each
  child mutation notes its change on the parent and the reader reads
  only the parent (theater-network-08, 1.4.0).

### 5. Return a per-caller view, not stored records

When items carry per-owner fields (`held_by`, deadlines, private notes)
and callers don't own every item, return a view model with
caller-relative fields computed from `context.auth`; the browser never
needs other users' IDs (cineloop-09, cineloop-18, 1.4.1):

```python
async def seat_map(
    self, context: ReaderContext,
) -> Showing.SeatMapResponse:
    me = context.auth.user_id if context.auth else None
    return Showing.SeatMapResponse(seats=[
        SeatView(
            label=seat.label,
            status=seat.status,
            mine=(me is not None and seat.held_by == me),
            hold_expires_at=(
                seat.hold_expires_at if seat.held_by == me else 0
            ),
        )
        for seat in self.state.seats
    ])
```

### 6. One reactive hook per component

N live subscriptions over a dynamic list = N child components, one hook
each ([`patterns-react-state.md`](patterns-react-state.md); cineloop-11,
cineloop-17).

## Never

- Return `self.state.<collection>` verbatim from a shared reader when
  items carry other users' identifiers — leaks them (step 5).
- Make an item its own `Type` because it is a domain noun with a status
  field — atomically co-changed items belong inline (step 1).
- Keep counters or indexes on a shared actor updated by every hold —
  every write queues on its lock; derive in a reader.
- Compute a user-visible transition only at read time — other viewers
  never see it; also commit it with a scheduled writer.
- Subscribe a list page to the detail reader of every row — declare a
  summary reader.
- Subscribe once per row when the rows share a parent — subscribe to a
  fan-out reader on the parent.

## Limits

- Transitive reactivity covers readers called from a subscribed reader;
  per reboot-crm-30 (1.6.0 source, not otherwise verified): unary
  readers only, dependencies re-tracked every execution, errors fall
  back to backoff polling.
- A fan-out reader of about 150 actors did not complete inside the
  request window (theater-network-08, 1.4.0).

## Scales as

- List-page payload and re-render cost scale with N × reader response
  size; pick the reader per page (step 3).
- Fan-out first-push and per-page subscription numbers:
  [`patterns-load-and-benchmarking.md`](patterns-load-and-benchmarking.md).

## Errors you will see

None known.

## See also

- [`patterns-load-and-benchmarking.md`](patterns-load-and-benchmarking.md) — fan-out and subscription numbers
- [`state-collections.md`](state-collections.md) — inline collection mechanics
- [`patterns-react-state.md`](patterns-react-state.md) — hooks and optimistic UI
