---
title: Schema Evolution Is Additive-Only on Deployed Applications
impact: CRITICAL
impactDescription: Backwards-incompatible API changes, even a reworded method description, stop an app with persisted state from booting
tags: api, schema, evolution, backwards-compatibility, migration, backfill, expunge, field tag
summary: "Only additive changes boot over persisted state, and even a reworded `description=` refuses; add fields, tags, methods and Types instead of changing them; expunge rules for dev and production."
step: api
applies: [mcp-ui, web-app, backend-only]
always: false
when: "changing an API that is deployed or has persisted state"
verified: 1.6.0
docs: ""
---

# Schema Evolution Is Additive-Only on Deployed Applications

## When you are here

You are about to change the API of an application that has persisted
state: a deployed app, or a `rbt dev run` session with
`--application-name=...`. On boot the runtime compares the current API
against the schema the state was written with; a backwards-incompatible
change refuses to boot. The gate is the same under `rbt dev run`,
`rbt serve` and Reboot Cloud. What you ship stays in the schema until
the data is expunged.

## Do this

### Check the change against the table

| Change | Compatible? |
| --- | --- |
| Add a new state `Type` | yes |
| Add a new method to an existing `Type` | yes |
| Add a field with a (zero-value) default | yes |
| Rename a field, keeping its `tag` | yes (data is keyed by tag) |
| Rename a request/response `Model` class | yes (names are internal) |
| Change a method between `Writer` and `Transaction` | yes, if other options (e.g. `factory=True`) are unchanged |
| Change a `Transaction`'s `mode=` | yes |
| Add or remove declared `errors=` | yes |
| Change `mcp=` options (add/remove/modify `Tool()`) | yes |
| Edit a field's or a `Type`'s description | yes (observed at 1.5.0) |
| **Edit a method's `description=`** | **NO** (it is part of the method's options) |
| Delete a state `Type` | **NO** |
| Rename a state `Type` | **NO** (a delete + an add) |
| Delete a method | **NO** |
| Rename a method | **NO** (a delete + an add) |
| Delete a field (state, request or response model) | **NO** |
| Change a field's `tag` | **NO** (a delete + an add) |
| Change a field's type | **NO** |
| Change `list[T]` ↔ scalar | **NO** |
| Add a field without a default, or remove a default from a field | **NO** |
| Any other method-kind change (e.g. `Writer` → `Workflow`) | **NO** |

States and methods are matched by name, so a rename is a delete plus
an add; fields are matched by `tag`. A field's
required-ness cannot change in either direction. Request and response
models follow the state-model field rules; the class names passed to
`request=` / `response=` are internal (generated names come from the
method name). Deletion is forbidden because state may hold data in any
field ever written, and tasks, workflows and clients call methods by
name.

### When you need a "change", add instead

**Change a method's signature or semantics** — add a new method,
migrate callers, keep the old one as a delegating shim. To move
`deposit(amount: float)` to integer cents:

```python
api = API(
    Account=Type(
        state=AccountState,
        methods=Methods(
            # Old method (`amount: float`, dollars): kept, since
            # removal — or making `amount` optional in favor of a
            # new `cents: int` field on the same request — would
            # be rejected. Its servicer implementation now
            # converts and delegates to the logic behind
            # `deposit_cents`. Its `description=` stays word for
            # word: rewording it is itself a rejected change.
            deposit=Writer(
                request=DepositRequest, response=None,
                description="Add funds, in dollars.",
                mcp=None,
            ),
            # New method with the corrected request shape
            # (`amount_cents: int`).
            deposit_cents=Writer(
                request=DepositCentsRequest, response=None,
                description="Add funds, in whole cents.",
                mcp=None,
            ),
        ),
    ),
)
```

**Change a field's type or shape** — add a field with a new `tag` and
migrate lazily in writers: when a writer touches an actor whose data is
only in the old field, copy it across. The old field stays declared and
reads as its zero value once unused.

```python
class CartState(Model):
    # Old shape: kept; no longer written.
    item_names: list[str] = Field(tag=1, default_factory=list)
    # New shape.
    items: list[CartItem] = Field(tag=2, default_factory=list)
```

**Add an ID field (child actor, `OrderedMap` index) to a `Type` with
existing actors** — allocate it lazily where first needed. A
`factory=True` constructor is a no-op on an existing actor, so the
field would stay `""` forever:

```python
async def add_flight(self, context: TransactionContext, request) -> None:
    if self.state.flights_index_id == "":
        self.state.flights_index_id = str(uuid4())
    await OrderedMap.ref(self.state.flights_index_id).insert(...)
```

Readers treat `""` as "no index yet".

**Add an index or counter over data that already exists** — ship the
backfill in the same change. Write it as an idempotent method that
derives its payload from persisted state (re-running seed-time
computations drifts: "today at 14:00" recomputed on a later day no
longer matches what `create` stored), and call it from `initialize`
under a versioned alias, `.idempotently("ledger-backfill-v2")`; bump the
suffix to re-run. Why `initialize` needs the alias is in
`lifecycle-initialize-hook.md`. Log what the backfill did.

**Restructure state across types** — add the new `Type` beside the old,
migrate actors on access (or via a `Workflow`), and leave the old one
inert.

**Plan for accretion.** What you add, you keep, in the API and the
generated clients. Name fields so the default is the zero value
(`show_tags`, not `hide_tags`); flipping a default later costs a second
field. Mark superseded fields in their (editable) field description.
Get method descriptions right before state first persists.

### Before changing a deployed API

- [ ] Only *adding* states, methods, and defaulted fields; no renames;
      no method `description=` edits; every field's `tag` and type kept?
- [ ] New ID fields allocated lazily; new indexes shipped with a backfill?
- [ ] Anything breaking: playbook used, or explicit confirmation that
      expunging all data is acceptable?

## Never

- Rewording a method's `description=` after state exists — boot is
  refused. Put evolving rules in the servicer method's docstring.
- Iterating on a state shape while `rbt dev run` watches — a hot
  restart can persist a seconds-old typo and the gate then rejects the
  fix. Write the final form in one edit, or stop the watcher.
- Allocating a new ID field only in the `factory=True` constructor of
  a type with existing actors — it is never back-filled.
- Calling a backfill bare from `initialize` — it runs once ever; if
  that run was a no-op it never runs again. Use a versioned alias.
- `rbt dev expunge` from a script without `--yes` — waits forever.
- `rbt dev expunge` while `rbt dev run` is live — stop the backend
  first.
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
  (import matches fields by name and refuses unknown ones).
- On Reboot Cloud a rejected `rbt cloud up` does not take the running
  version down.
- `Writer(factory=True)` → `Transaction(factory=True)`: the 1.6.0
  validator allows it (mode is ignored), but one project saw it refused
  at 1.6.0. Declare a factory as a `Transaction` from the start if it
  might ever construct another actor.

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
| `InvalidStateRefError: The 'state_id' option must be at least 1 character(s) long` | A new ID field was never back-filled | Allocate lazily |

Recovery: `rbt dev run` — fix the code, or `x`, or
`rbt dev expunge --application-name=<app> --yes`; `rbt serve` — delete
the data under `--state-directory`; Reboot Cloud —
`rbt cloud down --api-key=...` (brings the app down **and expunges its
state**), then `rbt cloud up`.

## See also

- [`state-collections.md`](state-collections.md) — ID fields for child actors
- [`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md) — versioned-alias backfills
- [`state-scalar-fields.md`](state-scalar-fields.md) — zero-value default rule
