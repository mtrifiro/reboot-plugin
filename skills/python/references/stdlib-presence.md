---
title: Track Online Subscribers with `Presence`
impact: MEDIUM
impactDescription: Connection-aware UIs need a durable presence model; rolling your own duplicates this
tags: stdlib, Presence, Subscriber, MousePosition, online, connected, usePresenceContext, MouseTracker
summary: "`Presence` registry and `Subscriber` connection tracking (plus `MousePosition`) for who-is-online UIs: register `presence.servicers()`; in React wrap the tree in `<Presence>` from `@reboot-dev/reboot-std-react/presence`."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "tracking who is connected (presence)"
verified: 1.6.0
docs: ""
---

# Track Online Subscribers with `Presence`

## When you are here

You need a who-is-online list (participants in a room, tabs on a
document) or collaborative cursors. The stdlib ships three cooperating
types for this, all importable from `reboot.std.presence.v1.presence`:

- **`Subscriber`** — one user/tab; counts live connections (`toggles`).
- **`Presence`** — the set of currently present subscriber IDs for one
  scope (e.g. a chat room).
- **`MousePosition`** — optional per-subscriber cursor position.

Do not hand-roll ping/pong: connection lifetime is a long-lived
`Subscriber.connect` reader whose cancellation the framework observes.

## Do this

### Register the servicers

```python
from reboot.std.presence.v1 import presence


async def main():
    await Application(
        servicers=[MyServicer] + presence.servicers(),
    ).run()
```

`presence.servicers()` returns
`[PresenceServicer, SubscriberServicer, MousePositionServicer]`. There
is no `presence_library()` at 1.6.0.

### Methods (1.6.0 proto)

| Type | Method | Kind | Request fields |
| --- | --- | --- | --- |
| `Subscriber` | `create` | writer | — |
| `Subscriber` | `connect` | reader | `nonce` — long-lived; returns only when cancelled |
| `Subscriber` | `toggle` | writer | `nonce` — bumps `toggles`, schedules `wait_for_disconnect` |
| `Subscriber` | `status` | reader | — → `present` (`toggles > 0`) |
| `Subscriber` | `wait_for_disconnect` | workflow | `nonce` — waits for `connect` to end, then decrements `toggles` |
| `Presence` | `create` | writer | — |
| `Presence` | `subscribe` | writer | `subscriber_id` — adds it, schedules `watch` |
| `Presence` | `list` | reader | — → `subscriber_ids` |
| `Presence` | `watch` | workflow | `subscriber_id` — removes it once `status` is no longer present |
| `MousePosition` | `update` | writer | `left`, `top` (int32) |
| `MousePosition` | `position` | reader | — → `left`, `top` |

### Connection lifecycle

The order the 1.6.0 React component uses (and any client must follow):

1. `Subscriber.ref(subscriber_id).create(context)` — once; `connect`
   is a reader and needs the actor to exist.
2. Pick a fresh `nonce` (a UUID) and open
   `Subscriber.ref(subscriber_id).connect(context, nonce=nonce)`. It
   stays open while the client is connected.
3. Concurrently, `Subscriber.ref(subscriber_id).toggle(context, nonce=nonce)`.
   If `connect` hasn't registered yet it aborts `NotFound`; retry.
4. `Presence.ref(scope_id).subscribe(context, subscriber_id=subscriber_id)`.

When the client goes away the `connect` call is cancelled;
`wait_for_disconnect` decrements `toggles` and `Presence.watch` removes
the subscriber from `subscriber_ids`. To reconnect, repeat from step 2
with a new nonce.

### React

`@reboot-dev/reboot-std-react` (npm, 1.6.0) wraps that whole protocol:

```tsx
import {
  MouseTracker,
  Presence,
  usePresenceContext,
} from "@reboot-dev/reboot-std-react/presence";

function Room({ roomId, me }: { roomId: string; me: string }) {
  return (
    <Presence id={roomId} subscriberId={me}>
      <Participants />
    </Presence>
  );
}

function Participants() {
  const { subscriberId, subscriberIds } = usePresenceContext();
  return <ul>{subscriberIds.map((id) => <li key={id}>{id}</li>)}</ul>;
}
```

`<MouseTracker arrow={<Cursor />}>…</MouseTracker>` (inside
`<Presence>`) publishes this subscriber's cursor and renders everyone
else's. The generated per-type hooks `usePresence`, `useSubscriber`
and `useMousePosition` are in `@reboot-dev/reboot-std-api` under
`presence/v1/presence_rbt_react.js`,
`presence/subscriber/v1/subscriber_rbt_react.js` and
`presence/mouse_tracker/v1/mouse_position_rbt_react.js`.

### Building on top

Your app's room/channel actor calls
`Presence.ref(channel_id).subscribe(context, subscriber_id=...)` and
`Presence.ref(channel_id).list(context)` to render participants.
Server-side Python uses the servicer API above; browser code uses the
React package.

## Never

- `from reboot.std.presence.subscriber.v1.subscriber import Subscriber`
  or `...mouse_tracker.v1.mouse_position` — those are proto package
  names, not Python modules (`ModuleNotFoundError`). Import all three
  types from `reboot.std.presence.v1.presence`.
- `import reboot.std.react.presence` — no such module. The React side
  is the npm package `@reboot-dev/reboot-std-react/presence`.
- `Subscriber.create(context, subscriber_id)` — `create` is a plain
  writer, not a constructor, so there is no class-level form. Use
  `Subscriber.ref(subscriber_id).create(context)`.
- Calling `presence.subscribe` before the subscriber has toggled — it
  aborts `FailedPrecondition` because `status` is not yet present.
- Reusing a `nonce` for a second `connect` while the first is open —
  it aborts `AlreadyExists`.
- Rolling your own heartbeat / ping-pong presence — use this protocol.

## Limits

- All three servicers' `authorizer()` returns `allow()` at 1.6.0: any
  caller can create, toggle, subscribe or update. Put a stricter check
  in your own room actor if membership matters.
- Disconnect tracking lives in process memory (`_disconnect_events` on
  the servicer class). A `toggle` must reach the same server process
  that holds its `connect`, which the long-lived call and the generated
  client arrange.
- `MousePosition.update` sets `context.sync = False`: positions trade
  durability for speed and may be lost on a crash.
- `@reboot-dev/reboot-std-react@1.6.0` imports `uuid` but does not list
  it in its `dependencies`; install `uuid` in the frontend if the
  bundler cannot resolve it.
- The React component retries `connect` with no backoff (a TODO in the
  1.6.0 source).

## Scales as

- Not measured. Each connected tab holds one open `connect` call and
  one `wait_for_disconnect` workflow; each `subscribe` adds one `watch`
  workflow per (scope, subscriber).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'reboot.std.presence.subscriber'` | Imported a proto package path | Import from `reboot.std.presence.v1.presence` |
| `ModuleNotFoundError: No module named 'reboot.std.react'` | Treated the React hooks as Python | Use `@reboot-dev/reboot-std-react/presence` in TS |
| `` `usePresenceContext` must be used within `Presence` `` | Hook called outside `<Presence>` | Wrap the tree in `<Presence id=… subscriberId=…>` |

## See also

- [`lifecycle-application-entry.md`](lifecycle-application-entry.md) — where `servicers=` is assembled
- [`react-generated-client.md`](react-generated-client.md) — how generated React hooks behave
- [`servicer-workflow-wait.md`](servicer-workflow-wait.md) — the `until` behind `watch`
