#!/usr/bin/env python3
"""Load a backup made by `scripts/backup.sh` into an application.

    uv run python scripts/restore.py dev exports/backups/dev-20261008-120000
    uv run python scripts/restore.py prod exports/backups/prod-20261008-120000 \\
        --migration <name> --apply

A dry run unless `--apply` is given: it reads the backup, says what it
would leave out and why, checks every line against the API the code in
this checkout has, checks the application is empty, and stops.
`--apply` writes the rewritten lines to a temporary directory and runs
`rbt import` on it. The whole procedure (back up, expunge, boot,
restore, boot again, compare) is
`python/references/lifecycle-backup-restore.md`.

What `rbt import` does, and this script works around (Reboot 1.6.0):

- It parses each state by field name against the running application's
  message types and refuses a name it does not know, stopping part-way.
  A backup taken before the API changed needs a migration
  (`scripts/migrations/`); the check here fails the same way, on this
  machine, before anything is sent.
- It overwrites an actor that already exists and never deletes one the
  backup lacks. So the only restore offered is into an application
  holding none of the types in `MUST_BE_EMPTY`: the one an expunge
  leaves.
- It starts every imported task that has not completed. A task the
  boot itself starts (a loop `initialize` begins on every boot) would
  then run twice; name it in `BOOT_TASKS` and it, its records and its
  pending dequeue are left out, so the boot after the restore starts
  one on the restored state.
- It puts idempotency records back under the keys they had. Those keys
  survive an expunge (they are seeded from the application's id), so a
  record the fresh boot wrote is replaced by the backup's. Name
  `initialize`'s aliases after what they act on, not after the boot.
- It constructs nothing, so a stdlib `SortedMap` emptied before the
  backup comes back unreadable; the restore leaves such maps out and
  the queue that used one makes a new one.

The boot after the import is part of the restore. Then
`scripts/compare_exports.py` proves the data is what it was.
"""

from __future__ import annotations

import argparse
import collections
import importlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [
    str(ROOT / "backend" / "src"),
    str(ROOT / "backend" / "api"),
    str(ROOT / "api"),
    str(ROOT / "scripts"),
]

Item = dict

# -- The project's settings --------------------------------------------------

# Types that must hold no actor before a restore, as full state type
# names (`counter.v1.Counter`). `None`: every type of the application's
# own servicers (`servicers/registry.py`). Narrow it when `initialize`
# creates actors on every boot, which a fresh application then holds.
MUST_BE_EMPTY: Optional[tuple[str, ...]] = None

# Tasks the boot starts, as (state type, method as the export spells it,
# PascalCase): left out with what they own, so the boot after the
# restore starts its own. e.g. {("jobs.v1.Jobs", "RunLoop")}
BOOT_TASKS: set[tuple[str, str]] = set()

# A package prefix the API no longer has -> the migration that moves
# it, so the check names the migration to run. e.g. {"old.v1.": "split"}
RETIRED_PACKAGES: dict[str, str] = {}

# -- Reboot's own types ------------------------------------------------------

APPLICATION_TYPE = "rbt.v1alpha1.application.Application"
QUEUE_TYPE = "rbt.std.collections.queue.v1.Queue"
SORTED_MAP_TYPE = "rbt.std.collections.v1.SortedMap"
SORTED_MAP_ENTRY_TYPE = "rbt.std.collections.v1.SortedMapEntry"

KINDS = ("state", "sorted_map_entry", "task", "idempotent_mutation")


def kind(item: Item) -> str:
    for name in KINDS:
        if name in item:
            return name
    raise ValueError(f"an export line with none of {KINDS}: {item}")


def state_id(item: Item) -> str:
    """The id after the routing prefix of a `state_ref`."""
    return str(item["state_ref"]).split(":", 1)[-1]


# --------------------------------------------------------------------------
# Where things are
# --------------------------------------------------------------------------


def application_url(env_name: str) -> str:
    """Where scripts/backup.sh exports from, so a restore goes back there."""
    if env_name == "dev":
        return os.environ.get("REBOOT_DEV_URL", "http://localhost:9991")
    ledger = ROOT / "deploy" / "ledger.jsonl"
    rows = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()] if ledger.exists() else []
    urls = [row["api_url"] for row in rows if row.get("api_url")]
    if not urls:
        raise SystemExit("deploy/ledger.jsonl records no api_url; see scripts/backup.sh")
    return str(urls[-1])


def load_backup(backup: Path) -> tuple[dict, dict[str, list[Item]]]:
    manifest_path = backup / "manifest.json"
    data = backup / "data"
    if not manifest_path.is_file() or not data.is_dir():
        raise SystemExit(
            f"{backup} is not a backup: expected manifest.json and data/ "
            "(made by scripts/backup.sh)"
        )
    manifest = json.loads(manifest_path.read_text())
    files: dict[str, list[Item]] = {}
    for path in sorted(data.glob("*.json")):
        with path.open() as lines:
            files[path.name] = [json.loads(line) for line in lines if line.strip()]
    if not files:
        raise SystemExit(f"{data} holds no *.json files")
    return manifest, files


def deploy_env() -> dict[str, str]:
    """`.deploy.env`, for the Cloud API key; never printed."""
    values: dict[str, str] = {}
    path = ROOT / ".deploy.env"
    if path.is_file():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("'\"")
    return values


# --------------------------------------------------------------------------
# What a restore leaves out
# --------------------------------------------------------------------------


class Dropped:
    """Every line left out, with the reason, for the report."""

    def __init__(self) -> None:
        self.reasons: collections.Counter = collections.Counter()

    def add(self, item: Item, reason: str) -> None:
        self.reasons[(reason, item["state_type"], kind(item))] += 1

    def lines(self) -> list[str]:
        return [
            f"  {count:6d}  {state_type} {item_kind}: {reason}"
            for (reason, state_type, item_kind), count in sorted(self.reasons.items())
        ]


def drop_boot_items(
    items: list[Item], dropped: Dropped, boot_tasks: set[tuple[str, str]]
) -> list[Item]:
    """The lines that belong to the boot, not to the data."""
    # The tasks the boot starts, which the backup had running.
    started = {
        item["task"]["task_id"]["task_uuid"]
        for item in items
        if "task" in item
        and (item["state_type"], item["task"].get("method")) in boot_tasks
        and item["task"].get("status") != "COMPLETED"
    }

    # The records those tasks own: the calls they made from inside a
    # workflow (`workflow_id`), and the boot's own record of starting
    # them (`task_ids`). Both point at a task that is not coming back.
    def owned(record: dict) -> bool:
        if record.get("workflow_id") in started:
            return True
        return any(t.get("task_uuid") in started for t in record.get("task_ids", []))

    owned_tasks: set[str] = set()
    for item in items:
        record = item.get("idempotent_mutation")
        if record is not None and owned(record):
            owned_tasks.update(t["task_uuid"] for t in record.get("task_ids", []) if "task_uuid" in t)

    kept: list[Item] = []
    for item in items:
        item_kind = kind(item)
        if item["state_type"] == APPLICATION_TYPE:
            # Reboot's own actor: the port, the dev tunnels, the tasks
            # that watch them. Every boot writes it afresh, and a dev
            # export's copy names the dev port.
            dropped.add(item, "the boot rebuilds it")
            continue
        if item_kind == "task":
            task = item["task"]
            uuid = task["task_id"]["task_uuid"]
            if uuid in started:
                dropped.add(item, "the boot starts its own")
                continue
            # A dropped task's blocked `dequeue` is a call with nothing to
            # do but wait for a task that is not coming back.
            if uuid in owned_tasks and item["state_type"] == QUEUE_TYPE and task.get("status") != "COMPLETED":
                dropped.add(item, "a dropped boot task's dequeue")
                continue
        if item_kind == "idempotent_mutation" and owned(item["idempotent_mutation"]):
            dropped.add(item, "owned by a dropped boot task")
            continue
        kept.append(item)
    return kept


def forget_empty_sorted_maps(items: list[Item], dropped: Dropped) -> list[Item]:
    """A sorted map with nothing in it is left out, and the queue that
    used it forgets it, so the queue builds a new one on its next
    enqueue.

    Reboot 1.6.0 creates the storage for a sorted map's entries when the
    map is constructed, and an import constructs nothing: it stores the
    map's (empty) state and its entries, if any. A map emptied before
    the backup comes back as an actor whose entries cannot be read
    ("Failed to find column family ... SortedMapEntry"). A queue whose
    `sorted_map_id` is blank is empty by definition and constructs its
    map on the first enqueue.
    """
    map_ids = [state_id(item) for item in items if "state" in item and item["state_type"] == SORTED_MAP_TYPE]
    entry_refs = [item["state_ref"] for item in items if "sorted_map_entry" in item]
    empty_maps = {m for m in map_ids if not any(m in ref for ref in entry_refs)}
    kept: list[Item] = []
    for item in items:
        if "state" in item and item["state_type"] == SORTED_MAP_TYPE and state_id(item) in empty_maps:
            dropped.add(item, "an emptied sorted map; its queue makes a new one")
            continue
        if "state" in item and item["state_type"] == QUEUE_TYPE:
            if item["state"].get("sorted_map_id") in empty_maps:
                item["state"].pop("sorted_map_id")
        kept.append(item)
    return kept


def apply_migration(
    items: list[Item], migrate: Optional[Callable[[Item], Optional[Item]]], dropped: Dropped
) -> list[Item]:
    if migrate is None:
        return items
    kept: list[Item] = []
    for item in items:
        result = migrate(item)
        if result is None:
            dropped.add(item, "the migration leaves it out")
        else:
            kept.append(result)
    return kept


def rewrite(
    files: dict[str, list[Item]],
    migrate: Optional[Callable[[Item], Optional[Item]]],
    dropped: Dropped,
    boot_tasks: Optional[set[tuple[str, str]]] = None,
) -> list[Item]:
    """Every file's lines together, then the passes.

    Together, because the rules pair lines that live on different
    servers, so in different files: a task in one and the queue it was
    blocked on in another. The migration goes first: the rules after it
    name types the way this checkout does.
    """
    items = [item for lines in files.values() for item in lines]
    kept = apply_migration(items, migrate, dropped)
    kept = drop_boot_items(kept, dropped, BOOT_TASKS if boot_tasks is None else boot_tasks)
    return forget_empty_sorted_maps(kept, dropped)


# --------------------------------------------------------------------------
# Checking every line against the API in this checkout
# --------------------------------------------------------------------------


def registry() -> dict[str, tuple[type, type]]:
    """`state_type` -> (message class, servicer class), the way the
    server builds its own: the application's servicers, the stdlib
    libraries it uses, and Reboot's memoize."""
    import reboot.aio.memoize as memoize
    from servicers.registry import SERVICERS, libraries

    servicers = list(SERVICERS) + list(memoize.servicers())
    for library in libraries():
        servicers += list(library.servicers())
    return {
        servicer.__state_type_name__: (servicer.__state_type__, servicer)  # type: ignore[attr-defined]
        for servicer in servicers
    }


def own_types() -> tuple[str, ...]:
    """The state types of the application's own servicers."""
    from servicers.registry import SERVICERS

    return tuple(sorted(servicer.__state_type_name__ for servicer in SERVICERS))  # type: ignore[attr-defined]


def snake(method: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", method).lower()


def validate(items: list[Item], known: dict[str, tuple[type, type]]) -> list[str]:
    from google.protobuf import json_format
    from rbt.v1alpha1 import database_pb2

    errors: list[str] = []
    for item in items:
        state_type = item["state_type"]
        item_kind = kind(item)
        where = f"{state_type} {state_id(item)}"
        if item_kind == "sorted_map_entry":
            if state_type != SORTED_MAP_ENTRY_TYPE:
                errors.append(f"{where}: raw bytes for a type that is not a sorted-map entry")
            continue
        if state_type not in known:
            retired = next((m for p, m in RETIRED_PACKAGES.items() if state_type.startswith(p)), None)
            if retired:
                errors.append(f"{where}: a type this checkout moved; add --migration {retired}")
            else:
                errors.append(f"{where}: no such state type in this checkout")
            continue
        message_class, servicer = known[state_type]
        try:
            if item_kind == "state":
                json_format.ParseDict(item["state"], message_class())
            elif item_kind == "task":
                json_format.ParseDict(item["task"], database_pb2.Task())
                method = item["task"].get("method", "")
                if not hasattr(servicer, snake(method)):
                    errors.append(f"{where}: task of `{method}`, which this checkout no longer has")
            else:
                json_format.ParseDict(item["idempotent_mutation"], database_pb2.IdempotentMutation())
        except json_format.ParseError as error:
            errors.append(f"{where} ({item_kind}): {error}")
    return errors


# --------------------------------------------------------------------------
# Refusals
# --------------------------------------------------------------------------


def refusal(source_env: str, target_env: str, *, rehearsal: bool) -> Optional[str]:
    """Why this backup may not go into this application, or None."""
    if source_env == "dev" and target_env == "prod":
        return (
            "a dev backup cannot go into production: its users are the "
            "Development picker's identities, and production's are the "
            "real provider's"
        )
    if source_env == "prod" and target_env == "dev" and not rehearsal:
        return "a production backup into the dev loop is a rehearsal; say so with --rehearsal"
    return None


def rbt() -> str:
    return str(Path(sys.executable).parent / "rbt")


def actors_present(url: str, state_type: str, env: dict[str, str]) -> int:
    done = subprocess.run(
        [rbt(), "inspect", "state", "list", f"--type={state_type}", f"--application-url={url}"],
        env=env, capture_output=True, text=True,
    )
    if done.returncode != 0:
        # `inspect` fans out to every replica, and a Cloud deployment
        # answers on its first replica before the others resolve.
        last = done.stderr.strip().splitlines()[-1] if done.stderr.strip() else "no output"
        raise SystemExit(
            f"refused: the application did not answer `rbt inspect state list` ({last}). "
            "On Reboot Cloud that is a deployment still starting: wait a minute and run again."
        )
    return len([line for line in done.stdout.splitlines() if line.strip()])


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    # Line by line, so the report reads in order around `rbt import`'s own output.
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("target", choices=("dev", "prod"), help="which application to load into")
    parser.add_argument("backup", type=Path, help="a directory made by scripts/backup.sh")
    parser.add_argument("--migration", help="a module in scripts/migrations/ to rewrite the lines with")
    parser.add_argument("--apply", action="store_true", help="really send it; a dry run otherwise")
    parser.add_argument("--rehearsal", action="store_true", help="a production backup into the dev loop")
    args = parser.parse_args()

    manifest, files = load_backup(args.backup)
    source_env = manifest.get("environment", "?")
    url = application_url(args.target)
    print(f"backup:  {args.backup}  ({source_env}, {manifest.get('taken_at')}, {manifest.get('git_rev', '')[:12]})")
    print(f"into:    {args.target}  {url}")

    why_not = refusal(source_env, args.target, rehearsal=args.rehearsal)
    if why_not:
        print(f"\nrefused: {why_not}")
        return 2

    migrate = None
    if args.migration:
        migrate = importlib.import_module(f"migrations.{args.migration}").migrate
        print(f"with:    migrations/{args.migration}.py")

    before: collections.Counter = collections.Counter()
    after: collections.Counter = collections.Counter()
    dropped = Dropped()
    for items in files.values():
        for item in items:
            before[(item["state_type"], kind(item))] += 1
    rewritten = rewrite(files, migrate, dropped)
    for item in rewritten:
        after[(item["state_type"], kind(item))] += 1

    print(f"\n{sum(before.values())} lines in, {sum(after.values())} out")
    for line in dropped.lines():
        print(line)
    print("\nwhat goes in:")
    for (state_type, item_kind), count in sorted(after.items()):
        print(f"  {count:6d}  {state_type} {item_kind}")

    errors = validate(rewritten, registry())
    if errors:
        print(f"\n{len(errors)} line(s) this checkout's API cannot take; a migration is needed:")
        for error in errors[:40]:
            print(f"  {error}")
        if len(errors) > 40:
            print(f"  ... and {len(errors) - 40} more")
        return 1
    print("\nevery line parses against this checkout's API")

    env = dict(os.environ)
    if args.target == "prod":
        env.setdefault("REBOOT_CLOUD_API_KEY", deploy_env().get("REBOOT_CLOUD_API_KEY", ""))
        if not env["REBOOT_CLOUD_API_KEY"]:
            print("\nrefused: no REBOOT_CLOUD_API_KEY in the environment or .deploy.env")
            return 2
    must_be_empty = MUST_BE_EMPTY if MUST_BE_EMPTY is not None else own_types()
    present = {t: actors_present(url, t, env) for t in must_be_empty}
    if any(present.values()):
        print(
            "\nrefused: the application is not empty: "
            + ", ".join(f"{n} {t}" for t, n in present.items() if n)
            + ". A restore goes into what an expunge leaves; rbt import would "
            "overwrite what is there and delete nothing."
        )
        return 2
    print(f"the application holds none of: {', '.join(must_be_empty)}")

    if not args.apply:
        print("\ndry run; add --apply to load it")
        return 0

    with tempfile.TemporaryDirectory(prefix="restore-") as tmp:
        # One file: `rbt import` routes every line by its ref, so the
        # per-server split the export made is not needed.
        with (Path(tmp) / "restored.json").open("w") as out:
            for item in rewritten:
                out.write(json.dumps(item) + "\n")
        print(f"\nimporting {sum(after.values())} lines ...")
        subprocess.run([rbt(), "import", f"--application-url={url}", f"--directory={tmp}"], env=env, check=True)
    print(
        "\nimported. Now restart the application so `initialize` runs over the "
        "restored data (dev: restart `rbt dev run`; prod: `rbt cloud up` "
        "again), then take a fresh backup and run scripts/compare_exports.py "
        "against this one (python/references/lifecycle-backup-restore.md)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
