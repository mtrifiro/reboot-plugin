---
title: Use `OrderedMap` for Distributed Sorted Key/Value Storage
impact: HIGH
impactDescription: Without a stdlib sorted map, large or paginated collections must be hand-rolled; misusing it hangs bulk loads or aborts first reads
tags: stdlib, OrderedMap, B-tree, collections, range, paginated, ordered, bulk insert, seeding
summary: "Sorted key/value map for large or paged collections: construct it explicitly when a read may come first, bulk `insert` with `Item`, design keys for your queries, page by last key."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "the design uses an `OrderedMap`"
verified: 1.6.0
docs: ""
---

# Use `OrderedMap` for Distributed Sorted Key/Value Storage

## When you are here

`state-collections.md` sent you to Shape C (unbounded, paginated or
ordered index of IDs). You are writing code that creates, fills and
pages an `OrderedMap` (`reboot.std.collections.ordered_map.v1.ordered_map`):
a B-tree of `(string key → value)` across many `Node` actors. Whether
to use one, and why its ID is a persisted field: `state-collections.md`.

## Do this

Register the library, persist the map's ID on the parent, insert from
a transaction, page with `range`. `ordered_map_library()` takes an
optional `authorizer=` (default `allow_if(all=[is_app_internal])`).

```python
from reboot.std.collections.ordered_map.v1.ordered_map import (
    OrderedMap, ordered_map_library,
)
from reboot.std.item.v1.item import Item
from uuid import uuid4
from uuid7 import create as uuid7


class BankServicer(Bank.Servicer):

    async def create(
        self, context: TransactionContext, request: CreateRequest,
    ) -> CreateResponse:
        self.state.account_ids_map_id = str(uuid4())
        # Construct up front only if a read may come before any insert;
        # otherwise the first `insert` constructs it.
        await OrderedMap.ref(self.state.account_ids_map_id).create(context)
        return CreateResponse()

    async def sign_up(
        self, context: TransactionContext, request: SignUpRequest,
    ) -> SignUpResponse:
        await OrderedMap.ref(self.state.account_ids_map_id).insert(
            context,
            key=str(uuid7()),                # time-ordered keys
            bytes=request.account_id.encode(),
        )
        # Bulk (seeds, batches): entries={key: Item(bytes=...), ...}
        return SignUpResponse()

    async def account_balances(
        self, context: ReaderContext, request: AccountBalancesRequest,
    ) -> AccountBalancesResponse:
        page = await OrderedMap.ref(self.state.account_ids_map_id).range(
            context, limit=32,
        )
        for entry in page.entries:
            key, value = entry.key, entry.bytes   # whichever field was set
        ...


async def main():
    await Application(
        servicers=[BankServicer, AccountServicer],
        libraries=[ordered_map_library()],
        initialize=initialize,
    ).run()
```

### Methods

| Method | Type | Signature |
| --- | --- | --- |
| `create` | transaction | `degree?: int = 128, maintain_size?: bool = False`; on a ref: `OrderedMap.ref(id).create(context)` |
| `insert` | transaction | single: `key: str` + one of `value` / `bytes` / `any`; bulk: `entries: dict[str, Item]`. May pass `degree` / `maintain_size` on implicit construction. |
| `remove` | transaction | single: `key: str`; bulk: `keys: list[str]` |
| `search` | reader | `key: str` → `SearchResponse(found: bool, value? / bytes? / any?)` |
| `range` | reader | `start_key?: str, limit: int` (required, non-zero) → `RangeResponse(entries, total_size?)` |
| `reverse_range` | reader | `start_key?: str, limit: int` (required, non-zero) |
| `stringify` | reader | debug; renders the tree |

### Values, keys, pages

- **Construction:** options on the first `insert` (`degree=`,
  `maintain_size=`) override defaults; later calls are validated
  against the stored configuration. `degree` (default 128): higher for
  shallower trees, lower for narrower.
- **Value field:** exactly one of `value` (`google.protobuf.Value`,
  e.g. `from_str(...)`), `bytes` (simplest for string IDs:
  `id.encode()`) or `any`. Bulk `entries` use the same `Item` as
  `Queue` / `Topic` (`stdlib-item.md`).
- **Keys are an API decision;** design them for your queries. A
  `date#origin#destination#...` key makes "flights on this route today"
  a prefix scan. A zero-padded counter (`f"{seq:012d}"` from a counter
  on the parent) is deterministic, sorts by insertion, and makes
  "newest first" a plain `reverse_range`. UUIDv7 sorts by time but is
  not deterministic.
- **Paging:** pass the last `entry.key` as the next `start_key`. It is
  inclusive: fetch `limit + 1` and skip the cursor row, or append
  `"\x00"` to the cursor.
- **`maintain_size=True`** (on `create` or first `insert`) returns
  `total_size` on each `range` but writes the root on every
  insert/remove, serializing all mutations. Opt in only if you need the
  count.
- **`Node`** actors are exported for custom traversal and debugging
  only; use the `OrderedMap` methods.

## Never

- `await OrderedMap.create(context, map_id)` — the class has no
  `create`; use `OrderedMap.ref(map_id).create(context)`.
- Omitting `ordered_map_library()` from `Application(libraries=[...])` —
  fails on first call with an unknown state type error; at startup
  with `Missing required libraries: reboot.std.collections.ordered_map.v1.ordered_map`
  when a library that needs it (e.g. `Ciphertext`) is registered.
- `OrderedMap.ref(f"{self.ref().state_id}-drafts")` — persist the ID
  as a field (`state-collections.md`).
- Calling `insert` / `create` / `remove` from a `Writer` — they take a
  `TransactionContext` (or workflow / external context).
- `create` then `insert` on the same map in one transaction — hung
  when bisected at 1.3.0 (not re-verified at 1.6.0). Let the first
  `insert` construct it, or `create` in an earlier transaction.
- Bulk-loading from concurrent transactions that insert into the same
  map — see Scales as; load one transaction at a time.
- Setting single-key (`key` + value) and bulk (`entries`) fields on one call,
  or more than one value field per entry — mutually exclusive.
- `from uuid7 import ...` without declaring `uuid7` in
  `pyproject.toml` — third-party, not part of `reboot`.

## Limits

- Reading (`search`, `range`, `reverse_range`) before construction
  aborts with `StateNotConstructed`; there is no `exists` reader and
  `search` does not answer `found=False`. Catch
  `OrderedMap.SearchAborted` / `RangeAborted` as empty, or construct
  up front.
- `range` / `reverse_range` require `limit > 0`.
- No exclusive start (`after_key`); see Paging.
- At 1.5.0 a `range` page could start up to 64 rows *before*
  `start_key` at a leaf boundary. The 1.6.0 leaf walk bisects to the
  first key ≥ `start_key`; dropping rows below the cursor is still a
  cheap guard, but judge "more pages" on the raw page size.
- `create` and construction options on `insert` raise `InvalidArgument`
  if `degree < 2`, or `StateAlreadyConstructed` if the map exists with
  different options.

## Scales as

- `rbt dev run`: a four-hop transaction (two reads, one create, one
  `insert`) took about 1.5 s including the effect-validation re-run
  (1.5.0); 193 such calls took nearly five minutes. Seed with one
  transaction per parent using bulk `entries=`, not one per row.
- Concurrent transactions inserting into one map queue on its node
  locks, time out and retry: four in flight gave about one sixth the
  throughput of sequential (1.5.0). "Concurrent writes scale" holds
  for independent writers, not overlapping transactions.
- Hundreds of inserts into one map in a single transaction can exceed
  the lock deadline: 138 actors plus inserts worked, 360 hung (1.4.1).
  Split into transactions of proven size, each with its own
  idempotency alias (`lifecycle-initialize-hook.md`).
- Key shape dominates query cost: dropping the leading key component
  turned a prefix scan into a whole-day scan plus fan-out, about 100x
  slower (load test at 1.4.1). Point reads of a well-keyed map: p50
  6 ms locally.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `OrderedMap.SearchAborted: aborted with 'StateNotConstructed'` | Read before the first `insert` / `create` (also `RangeAborted`) | `create` up front, or catch and treat as empty |
| `` Range requires a non-zero `limit` value. `` | `range(limit=0)` or no `limit` (`InvalidRangeError`) | Pass `limit=` |
| `"type[OrderedMap]" has no attribute "create"` | Called `create` on the class | `OrderedMap.ref(id).create(context)` |
| `` `degree` must be >= 2 `` | Bad construction option (`InvalidArgument`) | `degree >= 2` |
| `StateAlreadyConstructed` | `create` / first-`insert` options differ from the existing map | Drop the options or match them |
| `acquire_shared` … `CancelledError` (traceback through `ordered_map_servicer.py` `_Insert`) | Overlapping transactions waiting on node locks | Run the transactions sequentially |

## See also

- [`state-collections.md`](state-collections.md) — when to use one
- [`stdlib-item.md`](stdlib-item.md) — the `Item` value envelope
- [`servicer-transaction.md`](servicer-transaction.md) — locks and transaction size
