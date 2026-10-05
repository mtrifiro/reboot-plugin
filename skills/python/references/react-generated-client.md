---
title: The Generated React Client Contract
impact: HIGH
impactDescription: The exact hook, mutator, and error shapes `rbt generate --react=` emits — identical for web apps and MCP UIs
tags: react, hooks, generated, codegen, errors, typescript, partialRequest, aborted, subscription
summary: "What `rbt generate --react=` emits: `use<Type>()` overloads, three-field reader returns, mutations resolving to `{ response, aborted }` instead of throwing, typed errors, snake-to-camel naming."
step: frontend
applies: [mcp-ui, web-app]
always: false
verified: 1.6.0
docs: ""
---

# The Generated React Client Contract

## When you are here

Writing a React component against `rbt generate --react=<dir>` output
(identical in a browser SPA and an MCP host). File locations, backend
URL, sign-in:
[`web-app/references/react-client.md`](../../web-app/references/react-client.md)
or [`mcp-ui/references/react-scaffolding.md`](../../mcp-ui/references/react-scaffolding.md).
Idioms on top: [`patterns-react-state.md`](patterns-react-state.md).

**Do not read the generated `*_rbt_react.ts`** (tens of thousands of
lines).

## Do this

### What is emitted, per state type

For a state type `Foo`:

```ts
// With an id, the handle; without one, the default id (signed-in
// user, MCP session, or URL parameter).
export function useFoo(args: { id: string }): UseFooApi;
export function useFoo(args?: undefined): {
  foo: UseFooApi | undefined;      // named after the state type
  isLoading: boolean;
};

export interface UseFooApi {
  state_id: string;                // the resolved id
  mutators: FooMutators;
  idempotently: (args: { key: string }) => FooIdempotently;

  // Per Reader: a live subscription (accepts `{ suspense: true }`)…
  useBar(partialRequest?: Foo.PartialBarRequest): {
    response: Foo.BarResponse | undefined;
    isLoading: boolean;
    aborted: FooBarAborted | undefined;
  };
  // …and a one-shot call.
  bar(
    partialRequest?: Foo.PartialBarRequest,
    options?: { signal?: AbortSignal; retry?: boolean },
  ): Promise<ResponseOrAborted<Foo.BarResponse, FooBarAborted>>;

  // Per mutation; `.pending` lists its in-flight calls on this actor.
  baz(
    partialRequest?: Foo.PartialBazRequest,
    options?: { metadata?: any; idempotencyKey?: string },
  ): Promise<ResponseOrAborted<Foo.BazResponse, FooBazAborted>>;
}

// Per method, a typed error union you can switch on.
export type FooBazAbortedError = /* your declared errors | framework errors */;
export class FooBazAborted extends reboot_api.Aborted { /* .error, .message */ }
```

`Foo.PartialBazRequest` is not `Partial<…>` (see Limits).

### Naming

- Python snake_case → TypeScript camelCase for fields and methods
  (`from_index` → `fromIndex`, `open_task_count` → `openTaskCount`).
- Request and response types are Zod-validated.
- Failure type: `<Type><Method>Aborted`; `aborted.error.type` is the
  Python error class's name. Framework errors (`StateNotConstructed`,
  `Unknown`, timeouts) use the same `aborted`, so switch on `.type`.

### Readers return three fields

`response`, `isLoading` **and** `aborted` (a denied `authorizer()`
aborts; it doesn't throw).

- Guard data on `response !== undefined`; use `isLoading` for
  connection state. An aborted reader is `!isLoading` with no
  `response`; a reconnect is `isLoading` with a stale `response`.
- Disconnects auto-reconnect without surfacing as `aborted`; don't
  build an online/offline indicator from it.
- Readers are push subscriptions: any session's mutation re-renders
  every mounted reader. No polling or refetch.

### Mutations resolve, they do not throw

Branch on `aborted` in the resolved `{ response, aborted }`:

```tsx
const { aborted } = await foo.baz({ title });
if (aborted !== undefined) {
  // `aborted.error.type` is the Python error class's name.
  return show(aborted);
}
```

### Hook ids must be real on every render

No SWR-style "pass `undefined` to skip". Identity often resolves
asynchronously: guard at the parent, mount the child with a real id.

## Never

- `try { await foo.baz(…) } catch { … }` as the failure path —
  failure is in `aborted`, not `catch`. Still wrap the *handler* in `try/finally`
  (id minting, transport teardown, a deadline can throw), or a
  `setBusy(true)` never unwinds.
- `useFoo({ id: id || '__none__' })` while identity loads — every
  loading session subscribes to one shared actor.
- `ReturnType<typeof useFoo>` as a prop type — it's the no-argument
  overload (`{ foo, isLoading }`); use `UseFooApi`.
- `ids.map(id => useFoo({ id }))` — breaks the rules of hooks; render
  one child per id ([`patterns-react-state.md`](patterns-react-state.md)).
- `#` in a subscribed actor id — it rides a WebSocket URL and `#`
  truncates it as a fragment; `@`, `:`, `~` are safe (observed 1.4.0).
- An error model with no fields at 1.5.0 or earlier — the client throws at
  import (blank page); give it one field. Safe at 1.6.0 (codegen
  always emits the `type` literal).

## Limits

- **Request fields with no default are required.** At 1.6.0
  `Partial<Method>Request` is `z.input`: fields with a default
  (`default=""`, `0`, `False`, `None`, the first `Literal`, or
  `default_factory=list|dict`, the only defaults the pydantic API
  accepts) may be omitted; omitting any other fails `tsc` with TS2769,
  `{}` included. Before 1.6.0 (observed 1.4.1, 1.5.0) it was `z.infer`
  and *every* field was required: pass `cursor: ""`, `limit: 0`.
  Adding a field without a default breaks every call site.
- A model used in several places is emitted structurally per site; the
  copies are interchangeable, so derive a prop type from either
  (`Foo.ListResponse["planes"][number]`).
- A mutation resolves only after same-actor mounted readers observed
  it, so they already show the new state; other actors' readers update
  on their own push.
- On `UNAUTHENTICATED` a mutation refreshes the token and retries once.
- A subscribed reader is transitively reactive (verified 1.4.1 and
  1.6.0), so one aggregating reader can replace N subscriptions
  ([`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md)).
- Reactivity tracks committed writes only; a value computed from the
  clock (an expired hold) never pushes
  ([`patterns-react-state.md`](patterns-react-state.md)).
- Subscribing to an unconstructed actor aborts `StateNotConstructed`
  and retries about once a second forever, tearing the page's shared
  channel under every subscription (observed 1.4.0): construct, then
  mount. After `rbt dev expunge` open tabs freeze; reload them all.
- Each subscription holds a streaming fetch; HTTP/1.1 allows about 6
  per host (Reboot's warning names the fix: HTTP/2 via TLS).
- Transport: gRPC server-streaming over `https:`, else a WebSocket
  multiplex (local `http://`). Cross-origin WebSocket frames carry no
  cookies, so the session JWT rides in the request payload, not a
  `Cookie` header.

## Scales as

- Each push carries the whole reader response to every subscriber: 48
  cards on a reader returning 200 seats stream 48 × 200 records per
  change; an eight-integer summary reader doesn't (theater-chain, 1.4.1).
- Setup is ~100ms alone, slow in a burst on `rbt dev run` (48 over
  ~10s, 1.4.1; more in [`patterns-load-and-benchmarking.md`](patterns-load-and-benchmarking.md)):
  give each subscription its own loading state.
- One page-of-snapshots reader cut first paint from ~5–7s to ~1.5s
  (bluesky, 1.4.1); budgets in [`patterns-react-state.md`](patterns-react-state.md).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `state ID must have a length of at least 1` | An explicit-id hook got `id: ''` | Mount only once the id is real |
| `stateIdToRef` (in the stack) | An explicit-id hook got `id: undefined` | Same |
| `error TS2769` … `is missing the following properties` | Omitted a request field with no default (before 1.6.0, any field) | Pass it (Limits) |
| `Invalid discriminated union option at index "0"` | Field-less error model, 1.5.0 codegen; throws at import, blank page | Upgrade to 1.6.0, or add one field |
| `Failed to construct 'WebSocket'` | `#` in a subscribed actor id | Change the id scheme |
| `[Reboot] '<Type>.<Method>' aborted with` | Console warning on every aborted call | Expected; handle `aborted` |
| `[Reboot] Caught unknown exception: Not expecting stream to ever be done` | Open subscriptions during a dev-server restart | None; it reconnects |
| `Expecting either a response or a status` | The one case a mutation promise rejects | Transport failure; handle in `try/finally` |
| `Maximum update depth exceeded` | A derived array in an effect's deps | See [`patterns-react-state.md`](patterns-react-state.md) |

## See also

- [`patterns-react-state.md`](patterns-react-state.md) — optimistic UI, deadlines, budgets
- [`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md) — aggregating readers, backend side
- [`api-errors.md`](api-errors.md) — declaring the errors `aborted` carries
