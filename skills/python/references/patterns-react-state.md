---
title: React State on Top of Reactive Readers
impact: HIGH
impactDescription: Without these idioms a Reboot UI ships round-trip-gated clicks, spinners that never stop, hook-order crashes, and pages that mount sixty subscriptions
tags: react, patterns, optimistic, hooks, subscription, deadline, useEffect, newId, frontend
summary: "One reactive hook per component, subscribe to summaries, optimistic overrides, a deadline on every mutation, `newId()` for browser-minted ids, string dependencies for derived values."
step: any
applies: [mcp-ui, web-app]
always: false
verified: 1.6.0
docs: ""
---

# React State on Top of Reactive Readers

## When you are here

You have a component calling the generated client and need to decide
where client-side state lives: what to paint before the server
answers, how many subscriptions a page may open, what to do when a
call never returns. The hook and mutator shapes themselves are in
[`react-generated-client.md`](react-generated-client.md). The backend
half of the summary-reader pattern (one reader that fans out across
actors) is in
[`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md); this
file covers only the frontend side.

## Do this

### One reactive hook per component

When a page needs N live items, the parent maps over ids and renders
components; each component owns exactly one subscription.

```tsx
function Lobby({ ids }: { ids: string[] }) {
  return ids.map((id) => <ShowingCard key={id} id={id} />);
}

function ShowingCard({ id }: { id: string }) {
  const { response } = useShowing({ id }).useSummary();
  if (response === undefined) return <CardSkeleton />;  // per-card loading
  return <Card summary={response} />;
}
```

This is also what gives per-item re-render granularity: a push to one
showing re-renders one card. A component can be conditional, a hook
cannot, so "mount only once the actor exists / the id is real" is a
parent decision.

### Fewer subscriptions: subscribe to the summary

Past about 15 subscriptions on one page, stop adding hooks and
subscribe to one reader on the parent that returns all the cards
(cineloop: 60 streams → 12; theater-chain, bluesky, showtime and
reboot-crm all reached the same shape). Because a subscribed reader is
transitively reactive, the parent's reader still pushes when any child
changes. The frontend then holds one hook and renders plain props:

```tsx
function Lobby({ theaterId }: { theaterId: string }) {
  const { response } = useTheater({ id: theaterId }).useMarquee();
  if (response === undefined) return <LobbySkeleton />;
  return response.cards.map((c) => <Card key={c.showingId} summary={c} />);
}
```

Keep the full, fat reader for the detail page only. For long feeds,
one reader returns the first page of snapshots for first paint, and
per-item subscriptions are kept for the rows actually on screen.
Paint the previous session's data from a `localStorage` snapshot in
frame one if first paint still matters: write it through on every
push, read it once on mount; the push channel replaces it, so it needs
no invalidation.

### Optimistic overrides

A cross-actor transaction (plus dev-mode effect validation) takes a
perceptible beat. Paint the expected state on click; let the pushed
reader confirm it; drop each override once the snapshot agrees;
revert it if the mutation resolves `aborted`.

```tsx
function SeatMap({ showingId }: { showingId: string }) {
  const showing = useShowing({ id: showingId });
  const { response } = showing.useSeatMap();
  const [overrides, setOverrides] = useState<Record<string, string>>({});

  // Drop each override once the pushed snapshot agrees with it.
  useEffect(() => {
    if (response === undefined) return;
    setOverrides((prev) => {
      const next = { ...prev };
      for (const s of response.seats) if (next[s.id] === s.status) delete next[s.id];
      return Object.keys(next).length === Object.keys(prev).length ? prev : next;
    });
  }, [response]);

  async function hold(seatId: string) {
    setOverrides((o) => ({ ...o, [seatId]: "HELD" }));
    const { aborted } = await showing.hold({ seatIds: [seatId] });
    if (aborted !== undefined) {
      setOverrides(({ [seatId]: _, ...rest }) => rest);   // revert
      show(aborted);
    }
  }

  const statusOf = (s: Seat) => overrides[s.id] ?? s.status;
  // …render with statusOf(seat)
}
```

No refetch orchestration: readers are push-based, so reconciliation is
"compare with the latest push". When the override must be visible in
sibling components (seat map and cart rail), keep it in a small shared
store (`useSyncExternalStore`) instead of either component, and
disable any irreversible action (checkout, payment) while an override
is unconfirmed: optimistic UI may show a guess, never commit against
one. The generated `foo.baz.pending` array (in-flight calls with their
`request`) is an alternative source for same-actor overrides.

### A deadline on every mutation in a dev-loop UI

`rbt dev run --watch` restarts the backend on every save; a call in
flight across a restart can leave the browser promise unresolved
forever. Race every call against a deadline and unwind in `finally`:

```ts
export function withDeadline<T>(call: Promise<T>, ms = 20_000): Promise<T> {
  return Promise.race([
    call,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error("backend did not answer")), ms)),
  ]);
}

// `idempotencyKey`: minted once per user intent (e.g. `newId()` when
// the form opens), reused on every retry of that intent.
async function onSave() {
  setBusy(true);
  try {
    const { aborted } = await withDeadline(doc.save({ text }, { idempotencyKey }));
    if (aborted !== undefined) show(aborted);
  } catch {
    show("The backend didn't answer. Nothing is corrupted; try again.");
  } finally {
    setBusy(false);
  }
}
```

The deadline does not cancel the call; it may still commit. Reuse the
same `idempotencyKey` on the retry so it cannot apply twice (see
[`patterns-idempotency.md`](patterns-idempotency.md)).

### `newId()` for ids the browser mints

`crypto.randomUUID()` exists only on a secure origin. Opening the SPA
at Vite's `Network:` URL (`http://192.168.x.x:5173`) instead of
`localhost` makes it undefined and the click handler throws.
`getRandomValues` works everywhere:

```ts
export function newId(): string {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  const b = crypto.getRandomValues(new Uint8Array(16));
  b[6] = (b[6] & 0x0f) | 0x40;
  b[8] = (b[8] & 0x3f) | 0x80;
  const h = Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}
```

### Derived values in effect dependencies: use a string

Reader hooks re-render on every push, so `response.seats.filter(…)` is
a new array many times a second. Key effects on a derived primitive:

```tsx
const heldKey = response?.seats.filter((s) => s.held).map((s) => s.id).join(",") ?? "";
useEffect(() => { /* … */ }, [heldKey]);
```

## Never

- `ids.map((id) => useShowing({ id }))` — the hook count changes as the
  list grows from empty; React's rules of hooks break. Render a child
  component per id.
- Deriving a visible transition at read time only (a lapsed hold, an
  expired offer) — nothing was written, so no other subscriber is
  notified; it demos in one tab and fails in two. Commit it with a
  scheduled writer ([`scheduling-basic.md`](scheduling-basic.md)) and
  keep the lazy check too: the schedule gives liveness, the check gives
  correctness if the schedule is late.
- A derived array or object in a `useEffect` dependency list — spins
  into `Maximum update depth exceeded`. Depend on a derived string.
- `crypto.randomUUID()` unguarded — undefined off a secure origin. Use
  `newId()`.
- A mutation awaited with no deadline in a `--watch` dev loop — the
  button spins forever after a restart.
- A single page-level spinner over many subscriptions — they fill in
  progressively; show per-subscription loading.
- A refetch library or a poll alongside reader hooks — readers already
  push; a duplicate poll also spends the per-host connection budget.

## Limits

- Hooks cannot be conditional or counted dynamically; components can.
- Reactivity tracks committed writes, never computed values.
- A deadline is client-side only; the server call may still commit.
- `crypto.randomUUID` needs a secure origin (`https:` or `localhost`).

## Scales as

- Subscriptions per page: about 15 is where the source projects called
  it a smell (cineloop, theater-chain, 1.4.1). Measured ramps and
  payload costs are in
  [`react-generated-client.md`](react-generated-client.md) § Scales as.
- Overrides cost nothing on the server; they hide latency, they do not
  remove it.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Maximum update depth exceeded` | An effect depends on an array rebuilt on every reader push | Depend on a derived string |

## See also

- [`react-generated-client.md`](react-generated-client.md) — hook, mutator, error shapes
- [`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md) — summary reader, backend side
- [`scheduling-basic.md`](scheduling-basic.md) — commit time-based transitions
