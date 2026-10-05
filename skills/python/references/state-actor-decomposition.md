---
title: Split a State Type That Holds Multiple Concerns
impact: HIGH
impactDescription: One actor holding many unrelated concerns serializes all writers across them and turns the front door into a God actor.
tags: state, decomposition, responsibility, actors, front-door, serialization, contention, deadlock, cycle, ownership
summary: "Split a Type whose fields cluster by unrelated concern (auth, persona, background engine, cache) into separate Types, or its writers serialize and `User` becomes a God actor."
step: api
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Split a State Type That Holds Multiple Concerns

## When you are here

One state `Type` (often the front-door `User`) has accreted several
unrelated responsibilities, or you are about to add one more. One
`Type` should hold **one concern**. This is a runtime rule, not
hygiene: writers on one actor serialize (`servicer-writer.md`), so
unrelated concerns on one actor contend for nothing. Splitting a
**collection** of entities into per-item actors is the orthogonal
decomposition, in [`state-collections.md`](state-collections.md).

## Do this

### Signals that a `Type` holds more than one concern

- **Field clusters that don't move together.** Auth (phone, session
  token, login phase) churns at login; persona (display name, notes)
  when the profile is edited; engine config (monitoring active, poll
  interval, watched IDs) when configuration changes. No single reader
  needs all three.
- **A background workflow's writes contend with user actions** — the
  monitor writing "last scanned at" serializes against a persona edit.
- **Prefixed fields** (`monitoring_active`, `monitoring_poll_interval`,
  `monitoring_chat_ids`): the prefix is a concern asking to be a `Type`.
- **More than ~15 methods grouping by prefix** (`start_login`,
  `complete_login`, `set_persona`, `start_monitoring`, `scan_once`, …).
- **A transient cache** (picker snapshot, draft, UI hint) next to
  durable business state: different lifecycle and read pattern; give it
  its own `Type` or a stdlib `Item`.

### Split: the front door owns IDs, each concern is a `Type`

```python
class TelegramSessionState(Model):
    phone: str = Field(tag=1, default="")
    login_phase: str = Field(tag=2, default="")
    session_string: str = Field(tag=3, default="")
    phone_code_hash: str = Field(tag=4, default="")


class MonitoringManagerState(Model):
    active: bool = Field(tag=1, default=False)
    poll_interval_seconds: int = Field(tag=2, default=0)
    # IDs of monitored chats; chats are their own `Type` when they have
    # lifecycle/methods.
    monitored_chat_ids_index_id: str = Field(tag=3, default="")


class UserState(Model):
    display_name: str = Field(tag=1, default="")
    # IDs of the concern-specific actors this user owns.
    telegram_session_id: str = Field(tag=2, default="")
    monitoring_manager_id: str = Field(tag=3, default="")
```

The front door's constructor is a `Transaction(factory=True)` that
creates each concern actor once and stores its ID:

```python
class UserServicer(User.Servicer):

    async def create(
        self, context: TransactionContext, request: User.CreateRequest,
    ) -> None:
        if context.constructor:
            self.state.display_name = request.display_name
            session, _ = await TelegramSession.create(context)
            self.state.telegram_session_id = session.state_id
            manager, _ = await MonitoringManager.create(context)
            self.state.monitoring_manager_id = manager.state_id
```

Per-concern methods live on the concern's `Type` (login on
`TelegramSession`, the `monitor` workflow on `MonitoringManager`).
The front door keeps only: identity fields naming the actor itself,
the IDs of the concern actors it owns, and front-door methods —
typically `Transaction`s that locate or create concern actors and
return their IDs, plus user-scoped UI. "Front door" means entry point
plus delegation, not container for all state (`mcp-ui` skill, "User
and Application Types").

### Each fact has one owner

After a split, every fact (an account's domain, a seat holder's name)
must be written by exactly one `Type`. If two types each hold and
write a copy, delete the copy that has no reader, or make one type
the owner and have the other read it.

## Never

- Declare a constructor that may ever create another actor as a
  `Writer(factory=True)` — a writer cannot call another actor, and the
  later change to `Transaction` has been refused over persisted state
  (`api-schema-evolution.md` § Limits). Start with
  `Transaction(mode=Exclusive(), factory=True)`.
- Build a **writer cycle**: a transaction on `A` that writes `B`, while
  a transaction on `B` writes `A` (e.g. `Contact.update` writes the
  account's copy of a name while `Account.set_contact_role` holds the
  account and writes the contact). Two ordinary concurrent requests
  deadlock; no single-request test reproduces it. The cycle usually
  means a duplicated fact: delete the copy (see above) rather than
  invert the call.
- Put a new feature on `User` because it is the entry point — that is
  how the God actor grows.

## Limits

- Nothing reports a writer cycle: `rbt generate`, `mypy` and the
  dashboard call graph (which draws it) stay silent (observed at
  1.6.0). A reach-back through a workflow (`A` → `B`'s workflow →
  `.per_workflow` write to `A`) runs as its own later transaction and is
  not a cycle, though it greps the same.
- A factory `Transaction` that constructs another actor, itself called
  from another transaction, works at least two levels deep with no
  special handling (observed at 1.6.0).

## Scales as

- Writers on one actor serialize; writers on different actors run
  independently (`servicer-writer.md`). A split by concern removes
  contention between concerns with no other application change.
- Every write persists the whole actor (`state-collections.md` §
  Scales as), so a cache or engine field written often makes every
  write to its neighbours more expensive.

## Errors you will see

None known.

## See also

- [`state-collections.md`](state-collections.md) — per-item decomposition of collections
- [`state-nested-models.md`](state-nested-models.md) — store the ID, not the object
- [`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md) — reading across the split actors
