---
title: "The auto-constructed User.create is now a Transaction"
summary: "Change a User servicer's create override from a WriterContext to a TransactionContext."
kind: migration
audience: agent
applies: [mcp-ui, web-app, backend-only]
when: "a User servicer overrides create"
---

## The auto-constructed `User.create` is now a `Transaction`

The reserved `create` factory method on an auto-constructed `User`
state used to be a `Writer`; it is now a `Transaction`. An override of
it can now construct other state machines (call other Reboot services)
while a `User` is being created.

If a servicer that subclasses `User.Servicer` overrides `create` with
a `WriterContext` parameter, e.g.:

```python
async def create(self, context: WriterContext) -> None:
    ...
```

change the parameter type to `TransactionContext`:

```python
async def create(self, context: TransactionContext) -> None:
    ...
```

and import `TransactionContext` in place of the now-unused
`WriterContext` (drop the `WriterContext` import only if nothing else
in the file still needs it). Apps that do not override `create` need
no changes.
