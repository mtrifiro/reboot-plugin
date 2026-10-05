---
title: Split a State Type That Holds Multiple Concerns
impact: HIGH
impactDescription: One actor holding many unrelated concerns serializes all writers across them and turns the front door into a God actor.
tags: state, decomposition, responsibility, actors, front-door, serialization, contention, deadlock, cycle, ownership
summary: "A Type with unrelated field clusters serializes writers and grows a God `User`; split it into separate Types."
step: api
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Split a State Type That Holds Multiple Concerns

## When you are here

One state `Type` (often the front-door `User`) holds several unrelated
responsibilities, or you are about to add one. One `Type` holds **one
concern**, because writers on one actor serialize
(`servicer-writer.md`) and unrelated concerns would contend for nothing.
Splitting a **collection** into per-item actors is the orthogonal
decomposition: [`state-collections.md`](state-collections.md).

## Do this

### Signals that a `Type` holds more than one concern

- **Field clusters that don't move together**: auth (phone, session
  token, login phase) churns at login, persona (display name, notes) on
  profile edits, engine config (monitoring active, poll interval,
  watched IDs) on configuration. No reader needs all three.
- **A background workflow's writes contend with user actions** (the
  monitor's "last scanned at" serializes against a persona edit).
- **Prefixed fields** (`monitoring_active`, `monitoring_poll_interval`,
  `monitoring_chat_ids`): the prefix wants to be a `Type`.
- **More than ~15 methods grouping by prefix** (`start_login`,
  `complete_login`, `set_persona`, `start_monitoring`, `scan_once`, …).
- **A transient cache** (picker snapshot, draft, UI hint) beside durable
  state: different lifecycle; give it its own `Type` or a stdlib `Item`.

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
    monitored_chat_ids_index_id: str = Field(tag=3, default="")


class UserState(Model):
    display_name: str = Field(tag=1, default="")
    telegram_session_id: str = Field(tag=2, default="")  # owned concern actors
    monitoring_manager_id: str = Field(tag=3, default="")


class UserServicer(User.Servicer):

    # Transaction(factory=True): creates each concern actor once, stores its ID.
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

- Per-concern methods live on the concern's `Type` (login on
  `TelegramSession`, the `monitor` workflow on `MonitoringManager`).
- The front door keeps only its identity fields, the IDs of the concern
  actors it owns, and front-door methods (typically `Transaction`s that
  locate or create concern actors and return their IDs, plus
  user-scoped UI). "Front door" means entry point plus delegation
  (`mcp-ui` skill, "User and Application Types").

### Each fact has one owner

Every fact (an account's domain, a seat holder's name) is written by
exactly one `Type`. If two types each write a copy, delete the copy with
no reader, or make one the owner and have the other read it.

## Never

- Declare a constructor that may ever create another actor as a
  `Writer(factory=True)` — a writer cannot call another actor, and the
  later change to `Transaction` has been refused over persisted state
  (`api-schema-evolution.md` § Limits). Start with
  `Transaction(mode=Exclusive(), factory=True)`.
- Build a **writer cycle**: a transaction on `A` that writes `B`, while
  a transaction on `B` writes `A` (e.g. `Contact.update` writes the account's copy of a
  name while `Account.set_contact_role` holds the account and writes the
  contact). Two ordinary concurrent requests deadlock; `rbt generate`,
  mypy and single-request tests stay silent, and the dashboard's call
  graph draws the cycle without flagging it (reboot-crm-25, 1.6.0). It
  usually means a duplicated fact: pick the owner and delete the copy
  rather than invert the call. A return to A through `per_workflow` (a
  later transaction of its own) is not a cycle, though it greps the same.
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

- Writers on one actor serialize; on different actors they run
  independently (`servicer-writer.md`), so a split removes
  cross-concern contention with no other change.
- Every write persists the whole actor (`state-collections.md` §
  Scales as): a frequently written cache or engine field makes every
  neighbouring write more expensive.

## Errors you will see

None known.

## See also

- [`state-collections.md`](state-collections.md) — per-item decomposition of collections
- [`state-nested-models.md`](state-nested-models.md) — store the ID, not the object
- [`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md) — reading across the split actors
