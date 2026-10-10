#!/usr/bin/env python3
"""Tests for the templates' tests/harness_hygiene.py against stand-ins
for the Reboot modules it patches: the servers bind on loopback, the
test database's address dials `[::1]`, the model key placeholder
appears only when pydantic_ai is importable, and nothing breaks when
Reboot is not installed.

    python3 tests/templates/harness_hygiene_test.py
"""

import importlib.machinery
import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MODULE = ROOT / "skills" / "build" / "templates" / "web-app" / "tests" / "harness_hygiene.py"


def load(name: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, MODULE)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def fake_module(name: str, **attrs) -> types.ModuleType:  # type: ignore[no-untyped-def]
    module = types.ModuleType(name)
    module.__spec__ = importlib.machinery.ModuleSpec(name, None)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


class HarnessHygieneTest(unittest.TestCase):
    def setUp(self) -> None:
        self.saved = {k: sys.modules.get(k) for k in (
            "reboot", "reboot.controller", "reboot.controller.server_managers",
            "reboot.server", "reboot.server.database", "pydantic_ai")}
        self.key = os.environ.pop("ANTHROPIC_API_KEY", None)

    def tearDown(self) -> None:
        for k, v in self.saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
        if self.key is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = self.key

    def install_fake_reboot(self) -> tuple[types.ModuleType, type]:
        reboot = fake_module("reboot")
        controller = fake_module("reboot.controller")
        managers = fake_module("reboot.controller.server_managers", EVERY_LOCAL_NETWORK_ADDRESS="0.0.0.0")
        server = fake_module("reboot.server")

        class DatabaseServer:
            @property
            def address(self) -> str:
                return "0.0.0.0:4321"

        database = fake_module("reboot.server.database", DatabaseServer=DatabaseServer)
        reboot.controller, reboot.server = controller, server  # type: ignore[attr-defined]
        controller.server_managers, server.database = managers, database  # type: ignore[attr-defined]
        return managers, DatabaseServer

    def test_binds_loopback_and_dials_the_database_on_ipv6_loopback(self) -> None:
        managers, DatabaseServer = self.install_fake_reboot()
        sys.modules.pop("pydantic_ai", None)
        load("harness_hygiene_a")
        self.assertEqual(managers.EVERY_LOCAL_NETWORK_ADDRESS, "127.0.0.1")
        self.assertEqual(DatabaseServer().address, "[::1]:4321")
        self.assertNotIn("ANTHROPIC_API_KEY", os.environ, "no placeholder without pydantic_ai")

    def test_leaves_an_explicit_database_host_alone(self) -> None:
        _, DatabaseServer = self.install_fake_reboot()

        class Explicit(DatabaseServer):  # type: ignore[misc,valid-type]
            pass

        DatabaseServer.address = property(lambda self: "10.0.0.5:99")  # type: ignore[method-assign]
        load("harness_hygiene_b")
        self.assertEqual(Explicit().address, "10.0.0.5:99")

    def test_placeholder_key_only_with_pydantic_ai(self) -> None:
        self.install_fake_reboot()
        fake_module("pydantic_ai")
        load("harness_hygiene_c")
        self.assertEqual(os.environ.get("ANTHROPIC_API_KEY"), "test-placeholder")
        os.environ["ANTHROPIC_API_KEY"] = "real"
        load("harness_hygiene_d")
        self.assertEqual(os.environ["ANTHROPIC_API_KEY"], "real", "a real key is kept")

    def test_imports_without_reboot(self) -> None:
        for k in ("reboot", "reboot.controller", "reboot.controller.server_managers",
                  "reboot.server", "reboot.server.database", "pydantic_ai"):
            sys.modules[k] = None  # type: ignore[assignment]  # makes `import` raise ImportError
        load("harness_hygiene_e")


if __name__ == "__main__":
    unittest.main()
