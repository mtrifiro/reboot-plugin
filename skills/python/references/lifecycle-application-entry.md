---
title: Define the Application Entry Point
impact: CRITICAL
impactDescription: Application won't start without a correctly-shaped `main`
tags: main, application, asyncio, servicers, libraries
summary: "An `async def main()` that awaits `Application(servicers=[...], initialize=...).run()`; pass servicer classes, not instances; register stdlib libraries alongside your servicers."
step: shell
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Define the Application Entry Point

## When you are here

You are writing `backend/src/main.py`, the file `.rbtrc`'s
`dev run --application=` / `serve run --application=` line points at.
What `initialize` should do (seeding, singletons) is in
[`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md);
`.rbtrc` itself is in [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md).

## Do this

Every Reboot Python application has an `async def main()` that
constructs an `Application` with the list of Servicer classes and any
standard-library components, then awaits `.run()`. The `__main__`
block runs it under `asyncio.run`:

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

Combine your Servicer classes with stdlib `servicers()` factories, and
put each stdlib state type's `<name>_library()` in `libraries=[...]`:

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

A stdlib type is wired in **two** places: its `servicers()` list goes
into `servicers=[...]`, and its `<name>_library()` factory (where it
has one) goes into `libraries=[...]`. Each stdlib reference says
exactly what to register:

- [`stdlib-ordered-map.md`](stdlib-ordered-map.md) — `ordered_map.servicers()` + `ordered_map_library()`
- [`stdlib-queue.md`](stdlib-queue.md) — `queue.servicers()` + the stdlib map library (`Queue` uses a stdlib sorted-map actor under the hood)
- [`stdlib-pubsub.md`](stdlib-pubsub.md) — `pubsub.servicers()` (transitively pulls `queue.servicers()`) + the stdlib map library
- [`stdlib-presence.md`](stdlib-presence.md) — `presence.servicers()` (returns three Servicers; no library factory)

## Never

- `Application(servicers=[ChatRoomServicer()])` — an instance. Pass
  the **class**, `servicers=[ChatRoomServicer]`; Reboot constructs
  instances per actor as needed.
- `ChatRoomServicer().serve()` or a sync `main` with no `Application`
  wrapper — Reboot Servicers run inside the `Application`'s event
  loop; there is no other way to start them.
- Registering a stdlib type's `servicers()` but not its
  `<name>_library()` (or the reverse) — either omission is a runtime
  error about an unknown state type when the type is first called,
  not a startup check. Only a library whose own dependency library is
  missing fails at startup (`Missing required libraries: …`).

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
