---
title: Define the Application Entry Point
impact: CRITICAL
impactDescription: Application won't start without a correctly-shaped `main`
tags: main, application, asyncio, servicers, libraries
summary: "Pass servicer classes, not instances, and register stdlib libraries; `async def main()` awaiting `Application(servicers=[...], initialize=...).run()`."
step: shell
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Define the Application Entry Point

## When you are here

You are writing `backend/src/main.py`, the target of `.rbtrc`'s
`dev run --application=` / `serve run --application=` line
([`lifecycle-rbtrc.md`](lifecycle-rbtrc.md)). What `initialize` does:
[`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md).

## Do this

`async def main()` constructs an `Application` and awaits `.run()`;
`__main__` runs it under `asyncio.run`:

```python
import asyncio
import logging
from chat_room.v1.chat_room_rbt import ChatRoom
from chat_room_servicer import ChatRoomServicer
from reboot.aio.applications import Application
from reboot.aio.external import InitializeContext

logging.basicConfig(level=logging.INFO)

EXAMPLE_STATE_MACHINE_ID = 'reboot-chat-room'


async def initialize(context: InitializeContext):
    chat_room = ChatRoom.ref(EXAMPLE_STATE_MACHINE_ID)
    await chat_room.send(context, message="Hello, World!")


async def main():
    await Application(
        servicers=[ChatRoomServicer],
        initialize=initialize,
    ).run()


if __name__ == '__main__':
    asyncio.run(main())
```

### Multiple servicers and stdlib libraries

A stdlib type with a `<name>_library()` is wired once, in
`libraries=[...]`: the library registers its own servicers
(`OrderedMapLibrary`, verified 1.6.0). A type without one (`presence`)
lists its `servicers()` in `servicers=[...]`:

```python
import reboot.thirdparty.mailgun
from reboot.aio.applications import Application
from reboot.std.collections.ordered_map.v1.ordered_map import (
    ordered_map_library,
)


async def main():
    await Application(
        servicers=[AccountServicer, BankServicer]
        + reboot.thirdparty.mailgun.servicers(),
        libraries=[ordered_map_library()],
        initialize=initialize,
    ).run()
```

What each stdlib type registers:

- [`stdlib-ordered-map.md`](stdlib-ordered-map.md) — `ordered_map_library()` alone (it brings its servicers)
- [`stdlib-queue.md`](stdlib-queue.md) — `queue.servicers()` + the stdlib map library (`Queue` uses a stdlib sorted-map actor)
- [`stdlib-pubsub.md`](stdlib-pubsub.md) — `pubsub.servicers()` (pulls in `queue.servicers()`) + the stdlib map library
- [`stdlib-presence.md`](stdlib-presence.md) — `presence.servicers()` (three Servicers; no library factory)

### One list for the application and every test

Keep the list in `backend/src/servicers/registry.py` (the templates
ship it): `SERVICERS`, stdlib types' `servicers()` included, and a
`libraries()` function. `main.py` and every test module's `application`
fixture pass `servicers=SERVICERS, libraries=libraries()`, so a new
servicer is added once. A harness serving a type it never calls costs
nothing.

```python
# backend/src/servicers/registry.py
from reboot.std.collections.ordered_map.v1.ordered_map import (
    ordered_map_library,
)
from reboot.aio.servicers import Servicer
from servicers.bank import AccountServicer, BankServicer

# Typed: a one-servicer list would otherwise fail mypy against Application.
SERVICERS: list[type[Servicer]] = [AccountServicer, BankServicer]


def libraries() -> list:
    # A function, so each Application gets its own.
    return [ordered_map_library()]
```

## Never

- `Application(servicers=[ChatRoomServicer()])` — an instance. Pass the
  **class**; Reboot constructs instances per actor.
- A servicer list written out again in a test module — a type added
  to `main.py` and missed there fails only when a scenario calls it,
  with `Method not found!` (a new type missed in six harnesses broke
  every lead import; reboot-crm, 1.6.0).
- `ChatRoomServicer().serve()` or a sync `main` with no `Application` —
  Servicers run only inside the `Application`'s event loop.
- Omitting a stdlib type's `<name>_library()`, or a library-less
  type's `servicers()` — a runtime unknown-state-type error on first
  call, not a startup check. Only a library missing its
  own dependency library fails at startup (`Missing required libraries: …`).

## Limits

- None known.

## Scales as

- Not measured.

## Errors you will see

None known.

## See also

- [`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md) — first-run seeding and singletons
- [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md) — `.rbtrc` points at this file
- [`stdlib-ordered-map.md`](stdlib-ordered-map.md) — library registration, worked example
