"""Every servicer the application serves, and the stdlib libraries they
need: one list, for `main.py` and for every test module.

A servicer missing from an `Application`'s list fails only when
something calls it, with `Method not found!`, so a list copied into
each test module drifts without a word. Add a new servicer here, once.
"""

from reboot.aio.servicers import Servicer
from servicers.__app__ import CounterServicer, UserServicer

SERVICERS: list[type[Servicer]] = [UserServicer, CounterServicer]


def libraries() -> list:
    """The stdlib libraries the servicers need (`ordered_map_library()`
    for an `OrderedMap`, ...). A function, so each `Application` gets
    its own."""
    return []
