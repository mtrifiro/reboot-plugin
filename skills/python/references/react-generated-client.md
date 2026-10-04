---
title: The Generated React Client Contract
impact: HIGH
impactDescription: The exact hook, mutator, and error shapes `rbt generate --react=` emits — identical for web apps and MCP UIs
tags: react, hooks, generated, codegen, errors, typescript, partialRequest, aborted, subscription
step: frontend
applies: [mcp-ui, web-app]
always: false
verified: 1.6.0
docs: ""
---

# The Generated React Client Contract

## When you are here

You are writing a React component against the client
`rbt generate --react=<dir>` emitted. It is the same in a browser SPA
and inside an MCP host. Where the files live, how the backend URL is found and how
a user signs in are in
[`web-app/references/react-client.md`](../../web-app/references/react-client.md)
or
[`mcp-ui/references/react-scaffolding.md`](../../mcp-ui/references/react-scaffolding.md).
Idioms on top of this client are in
[`patterns-react-state.md`](patterns-react-state.md).

**Do not read the generated `*_rbt_react.ts`.** It runs to tens of
thousands of lines, each re-sent on every later turn.

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

`Foo.PartialBazRequest` is not `Partial<…>`: see Limits.

### Naming rules

Write the call before you read anything:

- Python snake_case → TypeScript camelCase, for fields and methods
  (`from_index` → `fromIndex`, `open_task_count` → `openTaskCount`).
- Request and response types are Zod-validated.
- A method's failure type is `<Type><Method>Aborted`, and
  `aborted.error.type` is the Python error class's name. Framework
  errors (`StateNotConstructed`, `Unknown`, timeouts) arrive through
  the same `aborted`, so switch on `.type` rather than assuming any
  abort is one of yours.

### Readers return three fields

`response`, `isLoading`, **and** `aborted`. A reader can abort — a
denied `authorizer()`, for instance — and that surfaces as `aborted`
rather than by throwing.

Guard on `response !== undefined` before touching data; use
`isLoading` for connection state. They diverge — an aborted reader is `!isLoading` with
no `response`, a reconnect is `isLoading` with a stale `response` — and
transport disconnects auto-reconnect without surfacing as `aborted`, so
don't build an online/offline indicator out of it.

Reader hooks are push-based subscriptions: when any session mutates
the state, every mounted reader re-renders. No polling, no refetch.

### Mutations resolve, they do not throw

They resolve to `{ response, aborted }`. Branch on `aborted`:

```tsx
const { aborted } = await foo.baz({ title });
if (aborted !== undefined) {
  // `aborted.error.type` is the Python error class's name.
  return show(aborted);
}
```

### Hook ids must be real on every render

An explicit-id hook is not SWR-style: there is no "pass `undefined` to
skip" mode. Identity often resolves asynchronously, so don't mount the
component until the id is real: guard at the parent and pass a
guaranteed-real id down.

## Never

- `try { await foo.baz(…) } catch { … }` as the failure path — a
  mutation's failure is in `aborted`; the `catch` catches nothing from
  it. Keep a `try/finally` around the *handler* anyway (id minting,
  transport teardown, a deadline can throw), or a `setBusy(true)`
  never unwinds.
- `useFoo({ id: id || '__none__' })` while identity loads — every
  loading session subscribes to the same shared actor. Mount the
  component only once the id is real.
- `ReturnType<typeof useFoo>` as a prop type — it resolves to the
  no-argument overload (`{ foo, isLoading }`). Type a handle as
  `UseFooApi`.
- `ids.map(id => useFoo({ id }))` — breaks the rules of hooks; render
  one child component per id (see
  [`patterns-react-state.md`](patterns-react-state.md)).
- `#` in a subscribed actor id — it rides a WebSocket URL and `#`
  truncates it as a fragment; `@`, `:`, `~` are safe (observed 1.4.0).
- An error model with no fields at 1.5.0 or earlier — the generated
  client threw at import (blank page). At 1.6.0 codegen always emits
  the `type` literal, so it is safe; on older pins give it one field.

## Limits

- **Request fields with no default are required.** `Partial<Method>Request`
  is the Zod schema's input type (`z.input`) at 1.6.0: a field declared
  with a default (`default=""`, `0`, `False`, `None`, the first
  `Literal`, or `default_factory=list|dict` — the only defaults the
  pydantic API accepts) may be left out; every other field must be
  passed, or `tsc` fails with TS2769, `{}` included. Before 1.6.0 (observed 1.4.1, 1.5.0) the type was
  `z.infer` and *every* field was required, defaulted or not; on those
  pins pass the empty value explicitly (`cursor: ""`, `limit: 0`).
  Adding a field without a default breaks every existing call site.
- A model used in several places is emitted structurally at each use
  site, not as one shared type. TypeScript's structural typing makes
  the copies interchangeable; derive a prop type from either
  (`Foo.ListResponse["planes"][number]`).
- A mutation's promise resolves only after the readers mounted on the
  same actor have observed it, so a same-actor reader already shows the
  new state when `response` arrives. A reader on another actor updates
  on its own push.
- On `UNAUTHENTICATED` a mutation refreshes the token and retries once.
- A subscribed reader is transitively reactive: it re-runs when any
  actor it read through other actors' readers changes (verified at
  1.4.1 and 1.6.0). One aggregating reader can replace N subscriptions;
  the backend shape is in
  [`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md).
- Reactivity tracks committed writes only. A value a reader computes
  from the clock (an expired hold) never pushes; see
  [`patterns-react-state.md`](patterns-react-state.md).
- A subscription to an unconstructed actor aborts `StateNotConstructed`
  and retries about once a second forever, tearing the page's shared
  channel under every other subscription (observed at 1.4.0).
  Construct it first, then mount the subscribing component. After
  `rbt dev expunge`, open tabs keep such subscriptions and freeze at
  their last frame: reload every tab after an expunge.
- Each reader subscription holds a streaming fetch; HTTP/1.1 allows
  about 6 per host, and Reboot logs a warning naming the fix (HTTP/2
  via TLS).
- Transport: gRPC server-streaming over `https:`, a WebSocket multiplex
  otherwise (a local `http://` dev server). Cross-origin WebSocket
  frames carry no cookies, so the session JWT rides in the request
  payload, not a `Cookie` header.

## Scales as

- Each pushed update carries the whole reader response, to every
  subscriber, on every change. Subscribing 48 cards to a reader that
  returns 200 seats streams 48 × 200 records per change; a summary
  reader of eight integers does not (theater-chain, 1.4.1).
- Subscription setup is cheap alone (~100ms) and slow in a burst on
  `rbt dev run`: 48 subscriptions filled in over ~10s; 60 took ~15s;
  50 had a slowest of ~6.8s (1.4.1). Give each subscription its own
  loading state; a page-level spinner sits through the whole ramp.
- One reader returning a page of snapshots cut first paint from
  ~5–7s to ~1.5s (bluesky, 1.4.1). Budget and fix:
  [`patterns-react-state.md`](patterns-react-state.md).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `state ID must have a length of at least 1` | An explicit-id hook got `id: ''` | Mount the component only once the id is real |
| `stateIdToRef` (in the stack) | An explicit-id hook got `id: undefined` | Same |
| `error TS2769` … `is missing the following properties` | A request field with no default (or, before 1.6.0, any field) was omitted | Pass the field; see Limits |
| `Invalid discriminated union option at index "0"` | A field-less error model, 1.5.0 codegen; module throws at import, page is blank | Upgrade to 1.6.0, or give the error model one field |
| `Failed to construct 'WebSocket'` | `#` in a subscribed actor id | Change the id scheme |
| `[Reboot] '<Type>.<Method>' aborted with` | Console warning on every aborted call | Handle `aborted`; the warning is expected |
| `[Reboot] Caught unknown exception: Not expecting stream to ever be done` | Each open subscription during a dev-server restart | None; it reconnects |
| `Expecting either a response or a status` | The one case a mutation promise rejects | Treat as transport failure in the handler's `try/finally` |
| `Maximum update depth exceeded` | A derived array in an effect's deps | See [`patterns-react-state.md`](patterns-react-state.md) |

## See also

- [`patterns-react-state.md`](patterns-react-state.md) — optimistic UI, deadlines, budgets
- [`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md) — aggregating readers, backend side
- [`api-errors.md`](api-errors.md) — declaring the errors `aborted` carries
