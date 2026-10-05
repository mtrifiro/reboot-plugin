---
title: Fan Out Calls with `Service.forall(ids).method(context)`
impact: MEDIUM
impactDescription: A hand-rolled gather is more code; an unbudgeted fan-out over ~150 actors times out
tags: rpc, forall, fan-out, batch, parallel, gather
summary: "Fan-out is one RPC per id, no batching; `Service.forall(ids).method(context)` over a hand-rolled gather; input order; budgets."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "fanning one call out to many actors"
verified: 1.6.0
docs: ""
---

# Fan Out Calls with `Service.forall(ids).method(context)`

## When you are here

Calling the same method on many actors of one type. Single calls and
context rules: `rpc-calls.md`; whether to fan out at all or read a copy
kept on the parent: `patterns-cross-actor-reads.md`.

## Do this

```python
from chat.v1.message_rbt import Message

# List of Message.GetResponse, in the order message_ids was iterated.
responses = await Message.forall(message_ids).get(context)
mine = [r.details for r in responses if r.details.author == request.name]

# Writes fan out the same way from a transaction or workflow (stdlib brokers do this):
await Queue.forall(queue_ids).enqueue(context, items=items)
```

- Returns a list of responses (a list of `None` for `response=None`).
- `ids` is any iterable of strings: list, set or generator.
- At 1.6.0 it is exactly
  `asyncio.gather(*[Service.ref(id).method(context, ...) for id in ids])`
  (generated code): shorter and idiomatic, not batched.

## Never

- Hand-rolling `asyncio.gather(*[Message.ref(mid).get(context) for mid
  in ids])` — same work, more code.
- Expecting framework-side batching — none at 1.6.0; one call per id.
- A subscribed reader that `forall`s over a large or growing set, or
  fans out to readers that fan out again — keep the facts on the parent
  (`patterns-cross-actor-reads.md`).
- `forall` over a writer from a `WriterContext` — as for a single call,
  writers and transactions need a `TransactionContext`,
  `WorkflowContext` or `ExternalContext` (`rpc-calls.md`).

## Limits

- Readers, writers and transactions only; not constructors or workflow
  methods (1.6.0 template).
- One failing call raises out of the `await`; the other calls are not
  cancelled and their responses are lost (plain `asyncio.gather`
  without `return_exceptions`, 1.6.0 template).
- A generator of ids is consumed once, at call time.
- A fan-out of about 150 actors does not finish inside the request
  window (theater-network-06; budget in
  `patterns-load-and-benchmarking.md`).

## Scales as

- Linear in ids: one concurrent RPC each; in dev each also crosses the
  local proxy, whose CPU cost is per request (theater-network-23,
  1.4.0). Times: `patterns-load-and-benchmarking.md`.

## Errors you will see

`Unavailable: ping timeout`: see `patterns-load-and-benchmarking.md`.

## See also

- [`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md) — when not to fan out
- [`patterns-load-and-benchmarking.md`](patterns-load-and-benchmarking.md) — measured fan-out budget
- [`rpc-calls.md`](rpc-calls.md) — context rules per method kind
