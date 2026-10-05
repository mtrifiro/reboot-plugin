---
title: Implement Reader Methods
impact: HIGH
impactDescription: A reader that mutates `self.state` loses the change silently; nested readers drop the caller's identity and multiply subscription cost
tags: servicer, reader, ReaderContext, state, async, reactive, transitive, fan-out
summary: "The reader signature must match the API file; mutating `self.state` is silently discarded; readers may call other readers, and a subscribed reader re-runs when any actor it read changes."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Implement Reader Methods

## When you are here

You are implementing a method declared `Reader(...)` in the API file:
it receives a `ReaderContext` and returns its declared response type
(nothing for `response=None`). The exact signature codegen requires
(base class, `request=None` / `response=None` variants, the two
lookalike shapes in the generated `*_rbt.py`) is in `api-methods.md`;
read it instead of the generated file.

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

Treat `self.state` as read-only. Readers on one actor run concurrently
and do not block each other; they wait for an in-flight writer or
transaction on that actor and resume after it completes.

A reader may call **readers** on other actors; the call takes the same
`context`:

```python
async def balance(account_id: str):
    account = Account.ref(account_id)
    balance = await account.balance(context)  # Account.balance is a reader
    return Balance(account_id=account_id, balance=balance.amount)
```

**Subscriptions are transitive.** A subscribed reader (a React hook,
a reactive call) re-runs when its own actor changes *and* when any
actor it read through other readers changes, including through
`forall` (verified at 1.6.0). One aggregating reader therefore
replaces N per-actor subscriptions. Its cost and depth rules are in
`patterns-cross-actor-reads.md`.

## Never

- Mutating `self.state` in a reader:

  ```python
  async def messages(self, context: ReaderContext) -> ChatRoom.MessagesResponse:
      self.state.messages.append("seen")  # NEVER
      return ChatRoom.MessagesResponse(messages=self.state.messages)
  ```

  It does not raise. The reader works on its own copy: the change
  shows up in that one response and is never persisted (observed at
  1.6.0: a reader set a field to 999 and returned it; the next read
  saw the old value). If it must change state, declare a `Writer` or
  `Transaction`.
- Calling a `Writer`, `Transaction` or constructor from a reader — a
  reader context may call only readers (`rpc-calls.md`). If the work
  is genuinely cross-actor, it is a `Transaction`.
- Computing "mine" from `context.auth` in a reader that another
  reader calls — the inner call is app-internal, `context.auth` is
  `None`, and the result is silently wrong, not an error. Pass the
  viewer explicitly; see `servicer-authorizer.md` § Never.
- `self.state_id` — use `self.ref().state_id` (`rpc-refs.md`).

## Limits

- A reader of an actor that was never constructed aborts with
  `StateNotConstructed` (`rpc-refs.md`).
- A fan-out reader of about 150 actors did not finish inside the
  request window; see `patterns-cross-actor-reads.md`.

## Scales as

- In dev, effect validation re-runs every nested inline reader, so a
  reader that fans out to readers that fan out multiplies at each
  level; details and the one-level rule are in
  `patterns-cross-actor-reads.md`.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `aborted with 'StateNotConstructed'` | The reader ran against an actor never constructed | Construct it first, or catch `<Method>Aborted` (`rpc-refs.md`) |
| `No overload variant matches argument types "ReaderContext"` | mypy: a reader called a writer, transaction or constructor | Move the work to a `Transaction` |

## See also

- [`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md) — fan-out depth, materialize on write
- [`servicer-authorizer.md`](servicer-authorizer.md) — nested calls carry no identity
- [`rpc-calls.md`](rpc-calls.md) — which context calls which method
