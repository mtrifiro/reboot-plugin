---
title: Fan Out Calls with `Service.forall(ids).method(context)`
impact: MEDIUM
impactDescription: A hand-rolled gather is more code; an unbudgeted fan-out over ~150 actors times out
tags: rpc, forall, fan-out, batch, parallel, gather
summary: "`Service.forall(ids).method(context)` instead of a hand-rolled gather: results in input order, one RPC per id (no batching), no constructors or workflows, budgeted fan-out."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "fanning one call out to many actors"
verified: 1.6.0
docs: ""
---

# Fan Out Calls with `Service.forall(ids).method(context)`

## When you are here

You need the same method called on many actors of one type: read every
message in a list, enqueue onto every subscribed queue. Single calls
and context rules are in `rpc-calls.md`; whether a reader should fan
out at all, or read a copy kept on the parent, is in
`patterns-cross-actor-reads.md`.

## Do this

```python
from chat.v1.message_rbt import Message

responses = await Message.forall(message_ids).get(context)

# `responses` is a list of `Message.GetResponse` in the same order
# as `message_ids`.
for mid, response in zip(message_ids, responses):
    print(mid, response.details)
```

`Service.forall(ids).method(context, **kwargs)` returns the list of
responses (a list of `None` for `response=None`) in the order the ids
were iterated. `ids` is any iterable of strings: list, set or
generator. At 1.6.0 it is exactly
`asyncio.gather(*[Service.ref(id).method(context, ...) for id in ids])`
(generated code); it is the shorter, idiomatic form, not a batched one.

Read-mostly fan-out is the canonical use:

```python
responses = await Message.forall(message_ids).get(context)
messages = [r.details for r in responses]
mine = [m for m in messages if m.author == request.name]
```

Writes fan out the same way from a transaction or workflow; stdlib
workflow brokers do this:

```python
await Queue.forall(queue_ids).enqueue(context, items=items)
```

## Never

- `asyncio.gather(*[Message.ref(mid).get(context) for mid in ids])` —
  it does the same work in more code; use `forall`.
- Expecting framework-side batching — there is none at 1.6.0; each id
  is a separate call.
- A subscribed reader that `forall`s over a large or growing set, or
  that fans out to readers that fan out again. Keep the facts on the
  parent instead (`patterns-cross-actor-reads.md`).
- `forall` over a writer from a `WriterContext` — same rule as a single
  call: writers and transactions need a `TransactionContext`,
  `WorkflowContext` or `ExternalContext` (`rpc-calls.md`).

## Limits

- Available for readers, writers and transactions; not for
  constructors or workflow methods (1.6.0 template).
- Context rules are those of a single call (`rpc-calls.md`).
- One failing call raises out of the `await`; the other calls are not
  cancelled and their responses are lost (plain `asyncio.gather`
  without `return_exceptions`, 1.6.0 template).
- A generator of ids is consumed once, at call time.
- A fan-out of about 150 actors does not finish inside the request
  window; the measured budget is in `patterns-load-and-benchmarking.md`
  (theater-network-06).

## Scales as

- Linear in the number of ids: one RPC each, run concurrently. In dev
  each call also crosses the local proxy, whose CPU cost is per request
  (theater-network-23, 1.4.0). Measured fan-out times are in
  `patterns-load-and-benchmarking.md`.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Unavailable: ping timeout` | The fan-out did not finish inside the request window | Materialize on write; see `patterns-cross-actor-reads.md` |

## See also

- [`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md) — when not to fan out
- [`patterns-load-and-benchmarking.md`](patterns-load-and-benchmarking.md) — measured fan-out budget
- [`rpc-calls.md`](rpc-calls.md) — context rules per method kind
