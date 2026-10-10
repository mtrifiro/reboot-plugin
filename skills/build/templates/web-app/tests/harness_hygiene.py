"""Settings every harness run needs on a developer's machine, applied
when `conftest.py` imports this module (the Reboot plugin's findings
P1.18 and P3.146); each one is skipped when what it patches is not
installed.

- Reboot's in-process test servers listen on `0.0.0.0`, which gRPC
  binds as one dual-stack IPv6 socket, and macOS hands such a socket
  an ephemeral port an orphaned Envoy may still hold on IPv4; a caller
  dialing `127.0.0.1:<port>` then reaches the orphan (`Unimplemented`
  404s, hangs). Binding the servers on `127.0.0.1` ends that. The test
  database has the mirror problem (a bare `TimeoutError` after about
  45 s from `DatabaseClient`); dialing it on `[::1]` reaches the socket
  it actually bound.
- `reboot.agents.pydantic_ai.Agent` wants `ANTHROPIC_API_KEY` at import,
  even when no call is made; a placeholder lets an offline run import
  it. A scenario that reaches the model with it fails on
  authentication, which is right: scenarios stand in for the model."""

import importlib.util
import os

try:
    from reboot.controller import server_managers

    server_managers.EVERY_LOCAL_NETWORK_ADDRESS = "127.0.0.1"
except ImportError:
    pass

try:
    from reboot.server import database

    _address = database.DatabaseServer.__dict__["address"]  # the property itself

    def _loopback_address(self) -> str:  # type: ignore[no-untyped-def]
        host, _, port = _address.fget(self).rpartition(":")
        return f"[::1]:{port}" if host in ("0.0.0.0", "[::]", "") else f"{host}:{port}"

    setattr(database.DatabaseServer, "address", property(_loopback_address))
except (ImportError, KeyError, AttributeError):
    pass

if importlib.util.find_spec("pydantic_ai") is not None:
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-placeholder")
