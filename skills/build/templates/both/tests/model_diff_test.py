"""`scripts/model_diff.py` sorts each change by the Reboot Flywheel's
routing rule: a domain-model change or a new or reworded rule goes back
to Design; a new scenario under an existing rule stays in Prove.

Run against a throwaway git repository with two revisions of a small
API and feature file. Generic: nothing here depends on this app's own
API, so it stays as the sample goes.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path

import model_diff

API_BEFORE = '''
from reboot.api import API, Field, Methods, Model, Reader, Type, Writer

class RoomState(Model):
    nights: list[str] = Field(tag=1, default_factory=list, description="Booked.")

RoomMethods = Methods(
    availability=Reader(request=None, response=None, description="Free?", mcp=None),
    book=Writer(request=None, response=None, description="Book.", mcp=None),
)

api = API(Room=Type(state=RoomState, methods=RoomMethods, description="A room."))
'''

API_AFTER = '''
from reboot.api import API, Field, Methods, Model, Reader, Transaction, Type, Writer

class RoomState(Model):
    nights: list[str] = Field(tag=1, default_factory=list, description="Booked.")
    rate: int = Field(tag=2, default=0, description="Per night.")

RoomMethods = Methods(
    availability=Reader(request=None, response=None, description="Free?", mcp=None),
    book=Transaction(request=None, response=None, description="Book.", mcp=None),
    release=Writer(request=None, response=None, description="Release.", mcp=None),
)

api = API(Room=Type(state=RoomState, methods=RoomMethods, description="A room."))
'''

FEATURE_BEFORE = """Feature: Guests book rooms
  A guest books a room for a night.

  Rule: A room is booked at most once per night

    @wip
    Scenario: A second guest requests a booked room
      Given room 204 is booked for November 14
      When another guest requests room 204 for that night
      Then the request is rejected

  Rule: A guest may cancel
    Scenario: A guest cancels
      Given a booking
      When the guest cancels
      Then the room is free
"""

FEATURE_AFTER = """Feature: Guests book rooms
  A guest books a room for a night.

  Rule: A room is booked at most once per night

    Scenario: A second guest requests a booked room
      Given room 204 is booked for November 14
      When another guest requests room 204 for that night
      Then the request is rejected

    Scenario: Two guests request the last room at once
      Given room 204 is free for November 14
      When two guests request it at the same moment
      Then exactly one is confirmed

  Rule: A guest may cancel
    Scenario: A guest cancels
      Given a booking
      When the guest cancels more than 48 hours ahead
      Then the room is free

  Rule: A multi-room reservation books every room or none
    Scenario: One room is unavailable
      Given room 205 is booked
      When a guest reserves rooms 204 and 205
      Then the reservation is rejected
"""

SERVICER_BEFORE = """
from reboot.aio.auth.authorizers import allow_if, has_verified_token, is_app_internal

def is_manager(context, **kwargs):
    return context.auth is not None and context.auth.properties.get("role") == "manager"

class RoomServicer(Room.Servicer):
    def authorizer(self):
        # Only the app books rooms, from the reservation.
        return Room.Authorizer(
            availability=allow_if(all=[has_verified_token]),
            book=allow_if(all=[is_app_internal]),
        )

class ReservationServicer(Reservation.Servicer):
    def authorizer(self):
        return allow_if(any=[is_manager, is_app_internal])

    async def cancel(self, context):
        pass
"""

SERVICER_AFTER = """
from reboot.aio.auth.authorizers import allow_if, has_verified_token, is_app_internal

def is_manager(context, **kwargs):
    return context.auth is not None

class RoomServicer(Room.Servicer):
    def authorizer(self):
        # A comment changed: not a rule.
        return Room.Authorizer(
            availability=allow_if(all=[has_verified_token]),
            book=allow_if(all=[has_verified_token]),
        )

class ReservationServicer(Reservation.Servicer):
    def authorizer(self):
        return allow_if(any=[is_manager, is_app_internal])

    async def cancel(self, context):
        print("a code change")

class GuestServicer(Guest.Servicer):
    def authorizer(self):
        return allow_if(all=[is_app_internal])
"""


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


class ModelDiffTest(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "api" / "hotel" / "v1").mkdir(parents=True)
        (self.root / "tests").mkdir()
        (self.root / "backend" / "src" / "servicers").mkdir(parents=True)
        self.servicer = self.root / "backend" / "src" / "servicers" / "hotel.py"
        self.servicer.write_text(SERVICER_BEFORE)
        self.api = self.root / "api" / "hotel" / "v1" / "hotel.py"
        self.feature = self.root / "tests" / "booking.feature"
        self.api.write_text(API_BEFORE)
        self.feature.write_text(FEATURE_BEFORE)
        git(self.root, "init", "-q")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "before")
        self.base = git(self.root, "rev-parse", "HEAD")
        self.saved_root = model_diff.ROOT
        model_diff.ROOT = self.root

    def tearDown(self) -> None:
        model_diff.ROOT = self.saved_root
        self.tmp.cleanup()

    def changes(self, head: str | None = None) -> list[model_diff.Change]:
        return model_diff.model_changes(
            model_diff.files_at(self.base, "api", ".py"),
            model_diff.files_at(head, "api", ".py"),
        ) + model_diff.auth_changes(
            model_diff.backend_files_at(self.base),
            model_diff.backend_files_at(head),
        ) + model_diff.feature_changes(
            model_diff.files_at(self.base, "tests", ".feature"),
            model_diff.files_at(head, "tests", ".feature"),
        )

    def test_no_change(self) -> None:
        self.assertEqual(self.changes(), [])
        self.assertIn("no change", model_diff.markdown("a", "b", []))

    def test_domain_model_changes_are_design(self) -> None:
        self.api.write_text(API_AFTER)
        found = {c.what: c.stage for c in self.changes()}
        self.assertEqual(found, {
            "`Room.book` method kind: Writer → Transaction": "design",
            "`Room.release` added, Writer": "design",
            "`RoomState.rate` added: `int`, tag 2": "design",
        })

    def test_feature_changes_sorted_by_the_routing_rule(self) -> None:
        self.feature.write_text(FEATURE_AFTER)
        found = {c.what: c.stage for c in self.changes()}
        path = "`tests/booking.feature`"
        self.assertEqual(found, {
            f'{path}: scenario "Two guests request the last room at once" '
            'added under existing rule "A room is booked at most once per night"': "prove",
            f'{path}: scenario "A second guest requests a booked room" no longer `@wip`': "prove",
            f'{path}: scenario "A guest cancels" steps changed (rule "A guest may cancel")': "design",
            f'{path}: rule "A multi-room reservation books every room or none" added, '
            "1 scenario": "design",
        })

    def test_who_may_call_changes_are_design(self) -> None:
        self.servicer.write_text(SERVICER_AFTER)
        found = {c.what: c.stage for c in self.changes()}
        self.assertEqual(found, {
            "who may call `Room.book` changed": "design",
            "who may call `Reservation` changed (`authorizer()`)": "design",
            "`Guest` gains an `authorizer()`": "design",
        })

    def test_generated_code_is_not_read(self) -> None:
        generated = self.root / "backend" / "api" / "hotel" / "v1"
        generated.mkdir(parents=True)
        (generated / "hotel_rbt.py").write_text(
            "class X:\n    def authorizer(self):\n        return None\n"
        )
        self.assertEqual(self.changes(), [])

    def test_committed_head(self) -> None:
        self.api.write_text(API_AFTER)
        git(self.root, "commit", "-q", "-am", "after")
        self.assertEqual(len(self.changes("HEAD")), 3)
        report = model_diff.markdown(self.base[:7], "HEAD", self.changes("HEAD"))
        self.assertIn("**3 design changes**", report)


if __name__ == "__main__":
    unittest.main()
