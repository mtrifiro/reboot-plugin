#!/usr/bin/env python3
"""Tests for the templates' scripts/api_lint.py: each thing it refuses,
named with its line and the fix; the three templates' own sample APIs
pass.

    python3 tests/templates/api_lint_test.py
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES = ROOT / "skills" / "build" / "templates"
LINT = TEMPLATES / "web-app" / "scripts" / "api_lint.py"

CLEAN = '''from reboot.api import API, Exclusive, Field, Methods, Model, Reader, Transaction, Type, Writer


class NotFound(Model):
    reason: str = Field(tag=1, default="")


class RoomState(Model):
    nights: list[str] = Field(tag=1, default_factory=list, description="Booked.")


api = API(
    Room=Type(
        state=RoomState,
        description="A room.",
        methods=Methods(
            availability=Reader(request=None, response=None, description="Free?", mcp=None, errors=[NotFound]),
            open=Transaction(mode=Exclusive(), request=None, response=None, description="Open.", mcp=None, factory=True),
            book=Writer(request=None, response=None, description="Book.", mcp=None),
        ),
    ),
)
'''


class ApiLintTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.api = Path(self.tmp.name) / "api"
        (self.api / "hotel" / "v1").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def lint(self, source: str, name: str = "hotel/v1/hotel.py") -> subprocess.CompletedProcess:
        path = self.api / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        return subprocess.run([sys.executable, str(LINT), str(self.api)], capture_output=True, text=True)

    def test_a_clean_api_passes(self) -> None:
        r = self.lint(CLEAN)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("pass", r.stdout)

    def test_the_templates_own_apis_pass(self) -> None:
        for template in ("web-app", "mcp-ui", "both"):
            r = subprocess.run([sys.executable, str(LINT), str(TEMPLATES / template / "api")],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{template}: {r.stdout}{r.stderr}")

    def test_a_reserved_method_name(self) -> None:
        r = self.lint(CLEAN.replace("book=Writer", "read=Writer"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("`read` is reserved", r.stdout)
        self.assertIn("hotel.py:", r.stdout)

    def test_a_reserved_name_on_user(self) -> None:
        r = self.lint(CLEAN.replace("Room=Type", "User=Type").replace("book=Writer", "set_claims=Writer"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("`set_claims` is a reserved method name on User", r.stdout)

    def test_a_reserved_name_in_a_methods_assignment(self) -> None:
        source = CLEAN.replace("methods=Methods(", "methods=RoomMethods,\n    )\n)\nRoomMethods = Methods(") \
            .replace("book=Writer", "schedule=Writer")
        source = source.split("RoomMethods = Methods(")[0] + "RoomMethods = Methods(" + \
            source.split("RoomMethods = Methods(")[1].split("\n        ),\n    ),\n)")[0] + "\n)\n"
        r = self.lint(source)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("`schedule` is reserved", r.stdout)

    def test_a_writer_factory_is_a_note(self) -> None:
        r = self.lint(CLEAN.replace("book=Writer(request=None", "book=Writer(factory=True, request=None"))
        self.assertEqual(r.returncode, 0, "a note, since a factory that constructs nothing else is fine")
        self.assertIn("note: a Writer(factory=True)", r.stdout)
        self.assertIn("Transaction(mode=Exclusive(), factory=True)", r.stdout)

    def test_a_bytes_field(self) -> None:
        r = self.lint(CLEAN.replace("nights: list[str]", "photo: bytes").replace("default_factory=list", 'default=b""'))
        self.assertEqual(r.returncode, 1)
        self.assertIn("a bytes field", r.stdout)

    def test_a_quoted_forward_reference(self) -> None:
        r = self.lint(CLEAN.replace("nights: list[str]", 'nights: list["Night"]'))
        self.assertEqual(r.returncode, 1)
        self.assertIn("quoted forward reference", r.stdout)
        self.assertIn("Python 3.10", r.stdout)

    def test_syntax_past_python_3_10(self) -> None:
        r = self.lint(CLEAN + "\ntype Alias = int\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("not Python 3.10", r.stdout)

    def test_an_error_model_with_no_fields(self) -> None:
        r = self.lint(CLEAN.replace('    reason: str = Field(tag=1, default="")', "    pass"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("error Model `NotFound` has no fields", r.stdout)

    def test_a_model_from_another_package(self) -> None:
        (self.api / "common" / "v1").mkdir(parents=True)
        (self.api / "common" / "v1" / "common.py").write_text(
            "from reboot.api import Field, Model\n\nclass Money(Model):\n    cents: int = Field(tag=1, default=0)\n")
        r = self.lint("from common.v1.common import Money\n" + CLEAN)
        self.assertEqual(r.returncode, 1)
        self.assertIn("imports from the API package `common`", r.stdout)
        self.assertIn("NameError", r.stdout)


if __name__ == "__main__":
    unittest.main()
