"""A backup restored into a fresh application holds what it was taken from.

The round trip a breaking-change deploy depends on (back up, expunge,
boot, restore, compare), run against the test harness with the real
export and import services, and with `scripts/restore.py`'s and
`scripts/compare_exports.py`'s own passes in between. A Reboot that
changes what an export holds, or a servicer whose state stops parsing
back, fails here rather than in production.

A harness test, not a feature file: a scenario runs in one application,
and a restore needs two. Replace the seeding (`seed`) with the app's
own types when the sample `count` goes; the rest is generic.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from __app__.v1.__app___rbt import User
from compare_exports import compare
from migrations.rules import drop_field
from rbt.v1alpha1.admin import export_import_pb2_grpc
from reboot.admin import export_import_client
from reboot.aio.applications import Application
from reboot.aio.auth.oauth import OAuth
from reboot.aio.auth.oauth_providers import (
    Development,
    OAuthProviderByEnvironment,
)
from reboot.aio.external import ExternalContext
from reboot.aio.tests import Reboot
from restore import Dropped, registry, rewrite, validate
from servicers.registry import SERVICERS, libraries

# The export and import services want the admin secret outside
# `rbt dev`, and the harness is outside it.
ADMIN = "an-admin-token-for-the-test"


def application() -> Application:
    development = Development()
    return Application(
        servicers=SERVICERS,
        libraries=libraries(),
        oauth=OAuth(
            provider=OAuthProviderByEnvironment(dev=development, prod=development),
            allowed_origins=[],
        ),
    )


def export_import(rbt: Reboot) -> export_import_pb2_grpc.ExportImportStub:
    context = ExternalContext(name="backup", bearer_token=ADMIN, url=rbt.url())
    return export_import_pb2_grpc.ExportImportStub(context.legacy_grpc_channel())


async def export_lines(rbt: Reboot) -> list[dict]:
    """What `scripts/backup.sh` writes to `data/`."""
    with tempfile.TemporaryDirectory() as tmp:
        await export_import_client.do_export(export_import(rbt), Path(tmp), admin_token=ADMIN)
        return [
            json.loads(line)
            for path in Path(tmp).glob("*.json")
            for line in path.read_text().splitlines()
            if line.strip()
        ]


async def import_lines(rbt: Reboot, lines: list[dict]) -> None:
    """What `scripts/restore.py --apply` sends."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "restored.json").write_text("".join(json.dumps(line) + "\n" for line in lines))
        await export_import_client.do_import(export_import(rbt), Path(tmp), admin_token=ADMIN)


async def seed(rbt: Reboot) -> dict[str, int]:
    """Some of every kind of the app's data; the values to expect back."""
    context = rbt.create_external_context(name="seed", app_internal=True)
    values = {"alice": 3, "bob": 5}
    for user_id, amount in values.items():
        # Sign-in constructs a `User`; outside it, `create` does.
        user, _ = await User.create(context, user_id)
        await user.increment(context, amount=amount)
    return values


class TestBackupRestore(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        os.environ["SECRET_REBOOT_ADMIN_TOKEN"] = ADMIN

    async def fresh(self) -> Reboot:
        """An application that is stopped however the test ends: one
        left running keeps its ports, and the next one fails on them."""
        rbt = Reboot()
        await rbt.start()
        self.addAsyncCleanup(rbt.stop)
        await rbt.up(application())
        return rbt

    async def test_a_restored_backup_holds_what_it_was_taken_from(self) -> None:
        before = await self.fresh()
        values = await seed(before)
        backup = await export_lines(before)

        dropped = Dropped()
        lines = rewrite({"backup.json": backup}, None, dropped, boot_tasks=set())
        self.assertEqual(validate(lines, registry()), [])

        # The expunge: a second, empty application on the same code.
        after = await self.fresh()
        await import_lines(after, lines)

        context = after.create_external_context(name="check", app_internal=True)
        for user_id, value in values.items():
            self.assertEqual((await User.ref(user_id).get(context)).value, value)
        result = compare(backup, await export_lines(after), {})
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["changed"], [])

    async def test_a_field_the_api_no_longer_has_needs_a_migration(self) -> None:
        before = await self.fresh()
        await seed(before)
        backup = await export_lines(before)

        # A backup from a release whose `UserState` had a field this
        # one dropped: `rbt import` would refuse it part-way, so the
        # check refuses it first.
        user_type = ""
        for item in backup:
            if "state" in item and item["state_type"].endswith(".User"):
                item["state"]["retired_field"] = 1
                user_type = item["state_type"]
        lines = rewrite({"backup.json": backup}, None, Dropped(), boot_tasks=set())
        errors = validate(lines, registry())
        self.assertTrue(errors)
        self.assertTrue(all("retired_field" in error for error in errors))

        # A migration that drops it makes the backup loadable again.
        migrate = drop_field(user_type, "retired_field")
        lines = rewrite({"backup.json": backup}, migrate, Dropped(), boot_tasks=set())
        self.assertEqual(validate(lines, registry()), [])
