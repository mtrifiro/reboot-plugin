---
title: Implement Reader Methods
impact: HIGH
impactDescription: A reader that mutates `self.state` loses the change silently; nested readers drop the caller's identity and multiply subscription cost
tags: servicer, reader, ReaderContext, state, async, reactive, transitive, fan-out
summary: "Mutating `self.state` in a reader is silently discarded; signature must match the API; reader-to-reader calls; subscription re-runs."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Implement Reader Methods

## When you are here

Implementing a method declared `Reader(...)`: it takes a
`ReaderContext` and returns its declared response (nothing for
`response=None`). Exact signature and variants: `api-methods.md` (read
it, not the generated `*_rbt.py`).

## Do this

```python
from chat_room.v1.chat_room_rbt import ChatRoom
from reboot.aio.contexts import ReaderContext


class ChatRoomServicer(ChatRoom.Servicer):

    async def messages(
        self,
        context: ReaderContext,
    ) -> ChatRoom.MessagesResponse:
        return ChatRoom.MessagesResponse(messages=self.state.messages)
```

- Treat `self.state` as read-only.
- Readers on one actor run concurrently; they wait for an in-flight
  writer or transaction on that actor.
- A reader may call **readers** on other actors with the same
  `context`: `await Account.ref(account_id).balance(context)`.
- **Subscriptions are transitive**: a subscribed reader (React hook,
  reactive call) re-runs when its own actor *or* any actor it read
  through other readers changes, including through `forall` (verified
  at 1.6.0). One aggregating reader replaces N per-actor subscriptions;
  cost and depth rules: `patterns-cross-actor-reads.md`.

## Never

- Mutating `self.state` (`self.state.messages.append("seen")  # NEVER`).
  It does not raise: the change appears in that one response and is
  never persisted (observed at 1.6.0: a reader set a field to 999 and
  returned it; the next read saw the old value). Use a `Writer` or
  `Transaction`.
- Calling a `Writer`, `Transaction` or constructor — a reader context
  calls only readers (`rpc-calls.md`); cross-actor work is a
  `Transaction`.
- Computing "mine" from `context.auth` in a reader another reader
  calls — the inner call is app-internal with `context.auth` `None`,
  silently wrong. Pass the viewer explicitly (`servicer-authorizer.md`
  § Never).
- `self.state_id` — use `self.ref().state_id` (`rpc-refs.md`).

## Limits

- Reading a never-constructed actor aborts `StateNotConstructed`
  (`rpc-refs.md`).
- A fan-out reader of about 150 actors did not finish inside the
  request window (`patterns-cross-actor-reads.md`).
- A reader fanning out from a read-mostly actor may return the other
  actors as of its own host's last write; a polled aggregator then
  showed a frozen world for minutes (agentic-demo, 1.4.0; not
  re-verified). Have the events that matter also write to the
  aggregator.

## Scales as

- In dev, effect validation re-runs every nested inline reader, so
  fan-out multiplies per level; the one-level rule is in
  `patterns-cross-actor-reads.md`.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `No overload variant matches argument types "ReaderContext"` | mypy: a reader called a writer, transaction or constructor | Move the work to a `Transaction` |

## See also

- [`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md) — fan-out depth, materialize on write
- [`servicer-authorizer.md`](servicer-authorizer.md) — nested calls carry no identity
- [`rpc-calls.md`](rpc-calls.md) — which context calls which method
