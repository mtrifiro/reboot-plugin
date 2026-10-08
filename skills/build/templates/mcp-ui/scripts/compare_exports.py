#!/usr/bin/env python3
"""Is the data after a restore the data that was backed up?

    uv run python scripts/compare_exports.py exports/backups/prod-<before> exports/backups/prod-<after>
    uv run python scripts/compare_exports.py --migration <name> <before> <after>

With `--migration`, the backup's type names go through that migration's
`TYPE_MAP` first, so a backup from before a package move compares
against an export from after it.

Compares every actor (`state` line) by type and id, except Reboot's
own `Application`, which every boot rewrites. An actor the backup had
and the fresh export lacks is a failure (exit 1). One the fresh export
has and the backup lacks is reported and not held against it: work
goes on after a restore. Fields that differ are listed; expect only
what the boot after the restore recomputes, and work that finished in
between.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

APPLICATION_TYPE = "rbt.v1alpha1.application.Application"
SORTED_MAP_TYPE = "rbt.std.collections.v1.SortedMap"

Actors = dict[tuple[str, str], dict]


def read_lines(backup: Path) -> list[dict]:
    data = backup / "data"
    if not data.is_dir():
        raise SystemExit(f"{backup} has no data/ (made by scripts/backup.sh)")
    return [
        json.loads(line)
        for path in sorted(data.glob("*.json"))
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def actors(lines: list[dict], type_map: dict[str, str]) -> tuple[Actors, list[str]]:
    """The actors by (type, id), and the refs of every sorted-map entry."""
    found: Actors = {}
    entry_refs: list[str] = []
    for item in lines:
        state_type = type_map.get(item["state_type"], item["state_type"])
        if "state" in item and state_type != APPLICATION_TYPE:
            found[(state_type, item["state_ref"].split(":", 1)[-1])] = item["state"]
        elif "sorted_map_entry" in item:
            entry_refs.append(item["state_ref"])
    return found, entry_refs


def compare(before_lines: list[dict], after_lines: list[dict], type_map: dict[str, str]) -> dict:
    """What the restore lost, added and changed."""
    (before, before_entries), (after, _) = actors(before_lines, type_map), actors(after_lines, {})
    # A sorted map that was empty in the backup is left out by
    # scripts/restore.py on purpose (its docstring says why), and the
    # queue that used it forgets it; that one absence is not a loss.
    left_out = sorted(
        key for key in set(before) - set(after)
        if key[0] == SORTED_MAP_TYPE and not any(key[1] in ref for ref in before_entries)
    )
    changed = []
    for key in sorted(set(before) & set(after)):
        if before[key] != after[key]:
            fields = sorted(
                f for f in set(before[key]) | set(after[key])
                if before[key].get(f) != after[key].get(f)
            )
            # The queue that forgot its emptied map differs by exactly that.
            if fields == ["sorted_map_id"] and before[key].get("sorted_map_id") in {k[1] for k in left_out}:
                continue
            changed.append((key, fields))
    return {
        "before": len(before),
        "after": len(after),
        "left_out": left_out,
        "missing": sorted(set(before) - set(after) - set(left_out)),
        "extra": sorted(set(after) - set(before)),
        "changed": changed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--migration", help="normalize type names through this migration's TYPE_MAP")
    args = parser.parse_args()
    type_map: dict[str, str] = {}
    if args.migration:
        type_map = importlib.import_module(f"migrations.{args.migration}").TYPE_MAP
    result = compare(read_lines(args.before), read_lines(args.after), type_map)

    print(f"{result['before']} actors before, {result['after']} after")
    if result["left_out"]:
        print(f"\nleft out by the restore, as intended ({len(result['left_out'])}):")
        for state_type, state_id in result["left_out"]:
            print(f"  {state_type} {state_id} (an emptied sorted map)")
    if result["missing"]:
        print(f"\nMISSING after ({len(result['missing'])}):")
        for state_type, state_id in result["missing"]:
            print(f"  {state_type} {state_id}")
    if result["extra"]:
        print(f"\nextra after ({len(result['extra'])}), not held against it:")
        for state_type, state_id in result["extra"]:
            print(f"  {state_type} {state_id}")
    if result["changed"]:
        print(f"\nchanged ({len(result['changed'])}):")
        for (state_type, state_id), fields in result["changed"]:
            print(f"  {state_type} {state_id}: {', '.join(fields)}")
    if not result["missing"] and not result["changed"]:
        print("\nevery actor the backup had is there, unchanged")
    return 1 if result["missing"] else 0


if __name__ == "__main__":
    sys.exit(main())
