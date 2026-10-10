---
title: Schema Evolution Is Additive-Only on Deployed Applications
impact: CRITICAL
impactDescription: Backwards-incompatible API changes, even a reworded method description, stop an app with persisted state from booting
tags: api, schema, evolution, backwards-compatibility, migration, backfill, expunge, field tag
summary: "Over persisted state only additive changes boot, even a reworded `description=` refuses; add fields/tags/methods/Types; expunge rules."
step: api
applies: [mcp-ui, web-app, backend-only]
always: false
when: "changing an API that is deployed or has persisted state"
verified: 1.6.0
docs: ""
---

# Schema Evolution Is Additive-Only on Deployed Applications

## When you are here

You are changing the API of an app with persisted state: a deployed app,
or `rbt dev run` with `--application-name=...`. On boot the runtime
compares the API against the schema the state was written with and
refuses a backwards-incompatible change — the same gate under
`rbt dev run`, `rbt serve` and Reboot Cloud. What you ship stays in the
schema until the data is expunged.

## Do this

### Check the change against the table

States and methods match by **name** (a rename is a delete plus an add);
fields match by **`tag`**. Deletion is forbidden because state may hold
any field ever written, and tasks, workflows and clients call methods by
name. Request/response models follow the state-model field rules.

| Compatible (boots) | **Incompatible (refused)** |
| --- | --- |
| Add a state `Type`, a method, or a field with a (zero-value) default | Delete or rename a state `Type` or a method |
| Rename a field, keeping its `tag` (data is keyed by tag) | Delete a field (state, request or response model) |
| Rename a request/response `Model` class (names are internal) | Change a field's `tag` or type, incl. `list[T]` ↔ scalar |
| `Writer` ↔ `Transaction`, other options unchanged (on a `factory=True` constructor see Limits; observed refused at 1.6.0) | Add a field without a default, or remove a default (required-ness can't change either way) |
| Change a `Transaction`'s `mode=` | Any other method-kind change (e.g. `Writer` → `Workflow`) |
| Add or remove declared `errors=` | **Edit a method's `description=`** (it is part of the method's options) |
| Change `mcp=` options (add/remove/modify `Tool()`) | |
| Edit a field's or a `Type`'s description (observed at 1.5.0) | |

### When you need a "change", add instead

**Change a method's signature or semantics** — add a new method, migrate
callers, keep the old one as a delegating shim. Moving
`deposit(amount: float)` to integer cents:

```python
api = API(
    Account=Type(
        state=AccountState,
        methods=Methods(
            # Old (`amount: float`, dollars): kept, because removing it or
            # making `amount` optional is refused. Its servicer converts and
            # delegates to `deposit_cents`. `description=` stays word for word.
            deposit=Writer(
                request=DepositRequest, response=None,
                description="Add funds, in dollars.",
                mcp=None,
            ),
            # New request shape (`amount_cents: int`).
            deposit_cents=Writer(
                request=DepositCentsRequest, response=None,
                description="Add funds, in whole cents.",
                mcp=None,
            ),
        ),
    ),
)
```

**Change a field's type or shape** — add a field with a new `tag`; in
writers, copy old-field data across on touch. The old field stays
declared and reads as its zero value once unused.

```python
class CartState(Model):
    item_names: list[str] = Field(tag=1, default_factory=list)  # old; no longer written
    items: list[CartItem] = Field(tag=2, default_factory=list)  # new
```

**Add an ID field (child actor, `OrderedMap` index) to a `Type` with
existing actors** — allocate it lazily, because a `factory=True`
constructor is a no-op on an existing actor and the field would stay
`""` forever. Readers treat `""` as "no index yet".

```python
async def add_flight(self, context: TransactionContext, request) -> None:
    if self.state.flights_index_id == "":
        self.state.flights_index_id = str(uuid4())
    await OrderedMap.ref(self.state.flights_index_id).insert(...)
```

**Add an index or counter over existing data** — ship the backfill in
the same change:
- An idempotent method deriving its payload from persisted state, not
  re-run seed computations ("today at 14:00" recomputed later drifts
  from what `create` stored).
- Called from `initialize` under a versioned alias,
  `.idempotently("ledger-backfill-v2")`; bump the suffix to re-run (why:
  `lifecycle-initialize-hook.md`). Log what it did.

**Restructure state across types** — add the new `Type` beside the old,
migrate on access (or via a `Workflow`), leave the old one inert.

**Plan for accretion** — what you add, you keep (API and generated
clients). Name fields so the default is the zero value (`show_tags`, not
`hide_tags`); flipping a default costs a second field. Mark superseded
fields in their (editable) field description. Get method descriptions
right before state first persists.

### Before changing a deployed API

- [ ] Only *adding* states, methods, and defaulted fields; no renames;
      no method `description=` edits; every field's `tag` and type kept?
- [ ] New ID fields allocated lazily; new indexes shipped with a backfill?
- [ ] Anything breaking: playbook used, or explicit confirmation that
      expunging all data is acceptable?

## Never

- Rewording a method's `description=` after state exists — boot is
  refused. Put evolving rules in the servicer method's docstring.
  Reboot intends to push an upstream fix that lets a method's description change after it is created; until a release says so, the rule holds.
- Iterating on a state shape while `rbt dev run` watches
  (`lifecycle-dev-loop.md` § Never).
- Allocating a new ID field only in the `factory=True` constructor of
  a type with existing actors — it is never back-filled.
- Calling a backfill bare from `initialize` — it runs once ever; if
  that run was a no-op it never runs again. Use a versioned alias.
- `rbt dev expunge` without `--yes`, or while `rbt dev run` is live
  (`lifecycle-rbtrc.md` § Never).
- Expunging a production application without explicit human
  confirmation.

## Limits

- The gate compares against whatever schema last booted.
- `--on-backwards-incompatibility` accepts only `ask` (default; press
  `x` to expunge), `expunge` (wipes automatically) and `fail` (waits for
  a code fix, never prompts); there is no "proceed". Deleting an unused
  method or a response-model field is rejected though it strands no data.
- Recovery is revert or expunge. Expunge irreversibly deletes all state;
  `rbt export` before and `rbt import` after can carry data across
  (import matches fields by name and refuses unknown ones): the
  procedure and scripts are
  [`lifecycle-backup-restore.md`](lifecycle-backup-restore.md).
- On Reboot Cloud a rejected `rbt cloud up` does not take the running
  version down.
- `Writer(factory=True)` → `Transaction(factory=True)`: the 1.6.0
  validator allows it (mode ignored), but it was observed refused at
  1.6.0. Declare a factory a `Transaction` from the start if it might
  ever construct another actor.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Updated state or method definitions are not backwards compatible.` | Boot refused; a list of changes follows (exit code 13 under `rbt dev run` / `rbt serve`) | Revert, then use the playbook; or expunge |
| `was deleted from servicer type` | A method was deleted or renamed | Restore it; keep as a shim |
| `Reboot options for method` … `updated from...` | A method's options changed, usually `description=` | Restore the exact old options |
| `was removed from Pydantic model` | A field was deleted (any model) | Restore it |
| `has switched type from` | A field's type changed | New field, new `tag` |
| ``waiting for modification, or hit `x` to expunge`` | `rbt dev run` with `ask` | Fix the code (reloads) or press `x` |
| `Reboot options for method 'create'` … `updated from... writer { constructor { } } to... transaction` | A factory constructor's kind cannot change against persisted state, though the kind change is compatible elsewhere | Keep the writer and construct the dependent actor lazily on first use; declare new factories `Transaction(mode=Exclusive(), factory=True)` |

Recovery: `rbt dev run` — fix the code, or `x`, or
`rbt dev expunge --application-name=<app> --yes`; `rbt serve` — delete
the data under `--state-directory`; Reboot Cloud —
`rbt cloud down --api-key=...` (brings the app down **and expunges its
state**), then `rbt cloud up`.

## See also

- [`state-collections.md`](state-collections.md) — ID fields for child actors
- [`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md) — versioned-alias backfills
- [`state-scalar-fields.md`](state-scalar-fields.md) — zero-value default rule
