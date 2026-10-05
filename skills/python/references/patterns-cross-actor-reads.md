---
title: Cross-Actor Reads and Reader Shape
impact: HIGH
impactDescription: Wrong actor boundaries turn one click into a distributed transaction; wrong reader shapes stream N full payloads to every list page or leak other users' data
tags: patterns, reader, reactive, fan-out, summary reader, view model, derived state, decomposition, cohesion
summary: "Run the cohesion test before splitting; derive projections; pair summary and detail readers; aggregate server-side one level deep; return per-caller views; one reactive hook per component."
step: any
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Cross-Actor Reads and Reader Shape

## When you are here

You are deciding whether a collection lives inline on one actor or as
an actor per item, whether a value is stored or derived, or what
readers a page over many actors should call. This file compares the
shapes. The mechanics of decomposition live in
`state-actor-decomposition.md` and `state-collections.md`; the numbers
behind "expensive" live in `patterns-load-and-benchmarking.md`.

## Do this

### 1. Run the cohesion counter-test before splitting a collection

The decomposition signals (identity, lifecycle, methods of its own) say
when to split. The counter-test says when not to: **must one user
action change several items all-or-nothing?** ("hold these 4 seats",
"move these 3 cards"). If yes, keep the items inline on one actor.

- Inline `list[Seat]` on one `Showing`: a multi-seat hold is one writer
  body, the 8-seat cap is checked in the same writer that grants it,
  two patrons racing for F-12 are ordered and the loser gets a typed
  error (cineloop-01, 1.4.1).
- Actor per seat: the same hold is a transaction over up to 8 actors.

Group into one actor what must change together; split what must scale
independently. Splitting does not help if every write still touches
one shared actor: per-seat actors plus occupancy counters kept on the
`Showing` by each hold convoyed 20 concurrent customers into
`Timed out waiting 30.0s to acquire exclusive lock`
(theater-network-01, 1.4.0). Keep bookkeeping off the write path and
derive it in a reader.

### 2. Derive what is a projection of state you already have

Before adding a state `Type` or field, ask whether it is computable
from existing state. A cart that is "the seats on this showing held by
me", computed in the reader, cannot disagree with the holds and needs
no cleanup when a hold expires (cineloop-02, 1.4.1). A wrong `Type` is
expensive: persisted schemas evolve additively only
(`api-schema-evolution.md`).

But **reactive updates track mutations, not computed values.** A
reader that decides at read time that a hold has lapsed changes no
state, so no other subscriber re-renders. Any transition other viewers
must see needs a writer that commits it: keep the lazy check for
correctness and add a scheduled writer for liveness (cineloop-03,
cineloop-16, 1.4.1; scheduling in `scheduling-basic.md`).

### 3. Declare summary and detail readers together

One actor can expose several readers at different granularities.
Reader shape is a performance API. A list page over N actors wants a
cheap summary; the detail page wants the full payload. Declare both
when you write the API, before the frontend exists:

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
frame, re-pushed on every hold; `summary` is the same actor, same
reactivity, about 2% of the payload (cineloop-10, 1.4.1; also
theater-chain-11).

### 4. Aggregate on the server, one level deep

A subscribed reader is **transitively reactive**: it re-runs when any
actor it read through another actor's reader (including `forall`)
changes. The public references do not say so; it is in the 1.6.0
source (`SidecarStateManager.reactively` installs `React` "providing
transitive reactivity") and was observed at 1.4.1 (showtime-27,
cineloop-28) and 1.6.0 (reboot-crm-30). So give the parent a reader
that fans out to its children's summaries and subscribe once:

```python
async def marquee(
    self, context: ReaderContext,
) -> Theater.MarqueeResponse:
    cards = await Showing.forall(self.state.showing_ids).summary(context)
    return Theater.MarqueeResponse(cards=cards)
```

Twelve `marquee` subscriptions replaced sixty per-showing ones
(cineloop-28, 1.4.1). Keep subscribed readers one fan-out deep: for a
second level, copy the facts the parent needs onto the parent, written
by the methods that change them (reboot-crm-31, 1.6.0). For a very
wide fan-out (about 150 children), materialize on write: each child
mutation notes its change on the parent, and the reader reads only
the parent's state (theater-network-08, 1.4.0).

### 5. Return a per-caller view, not stored records

When a collection carries per-owner fields (`held_by`, deadlines,
private notes) and callers do not own every item, declare a separate
view model and compute caller-relative fields against `context.auth`:

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

The browser never needs other users' IDs (cineloop-09, cineloop-18,
1.4.1).

### 6. One reactive hook per component

N live subscriptions over a dynamic list means N child components, each
calling exactly one hook. The frontend side is in
[`patterns-react-state.md`](patterns-react-state.md) (cineloop-11,
cineloop-17).

## Never

- Return `self.state.<collection>` verbatim from a shared reader when
  items carry other users' identifiers — it leaks them; return a view
  model (step 5).
- Make an item its own `Type` because it is a domain noun with a status
  field — if one action changes several items atomically, it belongs
  inline (step 1).
- Keep counters or indexes on a shared actor updated by every hold —
  that actor becomes the lock every write queues on; derive in a
  reader.
- Compute a user-visible transition only at read time — other viewers
  never see it; commit it with a scheduled writer too.
- Subscribe a list page to the detail reader of every row — declare a
  summary reader.
- Subscribe once per row when the rows share a parent — subscribe to a
  fan-out reader on the parent.

## Limits

- Transitive reactivity covers readers called from a subscribed reader.
  reboot-crm-30 (reading 1.6.0 source) adds: unary readers only, the
  dependency set is re-tracked on every execution, and errors fall back
  to backoff polling. Not otherwise verified here.
- A fan-out reader of about 150 actors did not complete inside the
  request window (theater-network-08, 1.4.0).

## Scales as

- Payload and re-render cost of a list page scale with N times the
  reader's response size: pick the reader shape per page (step 3).
- First push of a fan-out reader and subscription count per page:
  measured numbers in
  [`patterns-load-and-benchmarking.md`](patterns-load-and-benchmarking.md).

## Errors you will see

None known.

## See also

- [`patterns-load-and-benchmarking.md`](patterns-load-and-benchmarking.md) — fan-out and subscription numbers
- [`state-collections.md`](state-collections.md) — inline collection mechanics
- [`patterns-react-state.md`](patterns-react-state.md) — hooks and optimistic UI
