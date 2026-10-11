---
title: Track Online Subscribers with `Presence`
impact: MEDIUM
impactDescription: Connection-aware UIs need a durable presence model; rolling your own duplicates this
tags: stdlib, Presence, Subscriber, MousePosition, online, connected, usePresenceContext, MouseTracker
summary: "Register `presence.servicers()` and wrap React in `<Presence>` from `@reboot-dev/reboot-std-react/presence`; who-is-online via `Presence`, `Subscriber`, `MousePosition`."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "tracking who is connected (presence)"
verified: 1.6.0
docs: ""
---

# Track Online Subscribers with `Presence`

## When you are here

Building a who-is-online list (room participants, tabs on a document)
or collaborative cursors. Three types, all from
`reboot.std.presence.v1.presence`:

- **`Subscriber`** — one user/tab; counts live connections (`toggles`).
- **`Presence`** — the present subscriber IDs for one scope (e.g. a room).
- **`MousePosition`** — optional per-subscriber cursor.

Connection lifetime is a long-lived `Subscriber.connect` reader whose
cancellation the framework observes; no ping/pong.

## Do this

### Register the servicers

```python
from reboot.std.presence.v1 import presence


async def main():
    await Application(
        servicers=[MyServicer] + presence.servicers(),
    ).run()
```

It returns `[PresenceServicer, SubscriberServicer, MousePositionServicer]`;
there is no `presence_library()` at 1.6.0.

### Methods (1.6.0 proto)

| Type | Method | Kind | Request fields |
| --- | --- | --- | --- |
| `Subscriber` | `create` | writer | — |
| `Subscriber` | `connect` | reader | `nonce` — long-lived; returns only when canceled |
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

Any client must follow the 1.6.0 React component's order:

1. `Subscriber.ref(subscriber_id).create(context)` once (`connect` is a
   reader; the actor must exist).
2. Open `Subscriber.ref(subscriber_id).connect(context, nonce=nonce)`
   with a fresh UUID `nonce`; it stays open while connected.
3. Concurrently `Subscriber.ref(subscriber_id).toggle(context, nonce=nonce)`;
   it aborts `NotFound` until `connect` registers, so retry.
4. `Presence.ref(scope_id).subscribe(context, subscriber_id=subscriber_id)`.

On disconnect `connect` is canceled, `wait_for_disconnect` decrements
`toggles`, and `Presence.watch` removes the subscriber. Reconnect from
step 2 with a new nonce.

### React

`@reboot-dev/reboot-std-react` (npm, 1.6.0) wraps the protocol:

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
`<Presence>`) publishes this cursor and renders everyone else's.
Per-type hooks `usePresence`, `useSubscriber`, `useMousePosition` are
in `@reboot-dev/reboot-std-api` under
`presence/v1/presence_rbt_react.js`,
`presence/subscriber/v1/subscriber_rbt_react.js` and
`presence/mouse_tracker/v1/mouse_position_rbt_react.js`.

### Building on top

Your room actor calls
`Presence.ref(channel_id).subscribe(context, subscriber_id=...)` and
`Presence.ref(channel_id).list(context)`; browser code uses the React
package.

## Never

- `from reboot.std.presence.subscriber.v1.subscriber import Subscriber`
  or `...mouse_tracker.v1.mouse_position` — proto package names, not
  Python modules (`ModuleNotFoundError`); import from
  `reboot.std.presence.v1.presence`.
- `import reboot.std.react.presence` — no such module; React is npm
  `@reboot-dev/reboot-std-react/presence`.
- `Subscriber.create(context, subscriber_id)` — `create` is a plain
  writer, not a constructor; use `Subscriber.ref(subscriber_id).create(context)`.
- Calling `presence.subscribe` before the subscriber has toggled —
  aborts `FailedPrecondition` (`status` not yet present).
- Reusing a `nonce` for a second `connect` while the first is open —
  aborts `AlreadyExists`.
- Rolling your own heartbeat / ping-pong presence — use this protocol.

## Limits

- All three servicers' `authorizer()` returns `allow()` at 1.6.0: anyone
  can create, toggle, subscribe or update. Check membership in your own
  room actor.
- Disconnect tracking is in process memory (`_disconnect_events` on
  the servicer class): a `toggle` must reach the process holding its
  `connect` (the generated client arranges this).
- `MousePosition.update` sets `context.sync = False`: positions may be
  lost on a crash.
- `@reboot-dev/reboot-std-react@1.6.0` imports `uuid` without listing
  it in `dependencies`; install `uuid` if the bundler can't resolve it.
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
