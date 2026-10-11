#!/usr/bin/env python3
"""Check the plugin's manifests parse and its version pins agree.

Every JSON manifest the two agents read must parse. The plugin's
version is the Reboot version it pins (`bin/rbt`): a user who installs
a new plugin version gets that Reboot, and the templates must scaffold
onto the same one. Nothing else enforces that these say the same
thing, so this does:

* `VERSION`
* `.claude-plugin/marketplace.json` (`metadata.version`)
* `.codex-plugin/plugin.json`
* `bin/rbt` (`REBOOT_VERSION=`)
* `skills/build/templates/*/pyproject.toml` (`reboot==`, `reboot[dev]==`)

Each entry of `.claude-plugin/marketplace.json` with a local `source`
must match that plugin's own `.claude-plugin/plugin.json`: the same
`name`, and the same `version`. An entry with no version fails. The one
exception is the `reboot` plugin at the repo root, which has no version
in its entry or its `plugin.json`: a versioned install is keyed by the
version, and a local commit would no longer reach it.

`.agents/plugins/marketplace.json` (Codex) must have the Claude
marketplace's `name`; each local `source.path` must hold a
`.codex-plugin/plugin.json` with the entry's name, and every plugin it
lists must also be in the Claude marketplace.

Usage:
    tools/check-manifests.py        # exit 1 on a parse error or a disagreement
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MANIFESTS = [
    ".claude-plugin/marketplace.json",
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    "hooks/hooks.json",
    *sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("mods/*/.claude-plugin/plugin.json")),
    *sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("mods/*/hooks/hooks.json")),
]


def load(rel: str, problems: list[str]) -> dict | None:
    path = ROOT / rel
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append(f"{rel}: missing")
    except json.JSONDecodeError as e:
        problems.append(f"{rel}: invalid JSON ({e.msg} at line {e.lineno})")
    return None


def grep(rel: str, pattern: str, problems: list[str]) -> list[tuple[str, str]]:
    """Every match of `pattern`'s first group in the file, as (where, value)."""
    path = ROOT / rel
    if not path.is_file():
        problems.append(f"{rel}: missing")
        return []
    found = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = re.search(pattern, line)
        if m:
            found.append((f"{rel}:{n}", m.group(1)))
    if not found:
        problems.append(f"{rel}: no match for {pattern!r}")
    return found


def own_manifest(source: str, kind: str) -> tuple[str, dict | None]:
    """(relative path, parsed JSON or None) of the plugin.json under `source`."""
    path = (ROOT / source / kind / "plugin.json").resolve()
    shown = str(Path(source) / kind / "plugin.json")
    try:
        return shown, json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, NotADirectoryError):
        return shown, None
    except json.JSONDecodeError:
        return shown, {}


def is_root(source: str) -> bool:
    return (ROOT / source).resolve() == ROOT.resolve()


def claude_entry_problems(market: dict) -> list[str]:
    where = ".claude-plugin/marketplace.json"
    problems = []
    for entry in market.get("plugins", []):
        name, source = entry.get("name"), entry.get("source")
        if not isinstance(source, str) or not source.startswith("."):
            continue  # not a local plugin
        shown, own = own_manifest(source, ".claude-plugin")
        if own is None:
            problems.append(f"{where}: {name}'s source has no {shown}")
            continue
        if own.get("name") != name:
            problems.append(f"{where}: entry {name!r}, but {shown} names {own.get('name')!r}")
        if is_root(source):
            for label, doc in ((f"{where}: {name}", entry), (shown, own)):
                if "version" in doc:
                    problems.append(f"{label} has a version; the root plugin has none "
                                    f"(an install keyed by version misses local commits)")
            continue
        if "version" not in entry:
            problems.append(f"{where}: {name} has no version ({shown} says {own.get('version')})")
        elif own.get("version") != entry["version"]:
            problems.append(f"{where}: {name} is {entry['version']}, {shown} says "
                            f"{own.get('version')}")
    return problems


def codex_marketplace_problems(codex: dict, market: dict) -> list[str]:
    where = ".agents/plugins/marketplace.json"
    problems = []
    if codex.get("name") != market.get("name"):
        problems.append(f"{where}: name {codex.get('name')!r}, but the Claude marketplace "
                        f"is {market.get('name')!r}")
    claude_names = {e.get("name") for e in market.get("plugins", [])}
    for entry in codex.get("plugins", []):
        name, source = entry.get("name"), entry.get("source") or {}
        if name not in claude_names:
            problems.append(f"{where}: {name} is not in .claude-plugin/marketplace.json")
        if isinstance(source, dict) and source.get("source") == "local":
            shown, own = own_manifest(source.get("path", ""), ".codex-plugin")
            if own is None:
                problems.append(f"{where}: {name}'s path has no {shown}")
            elif own.get("name") != name:
                problems.append(f"{where}: entry {name!r}, but {shown} names {own.get('name')!r}")
    return problems


def main() -> int:
    problems: list[str] = []
    docs = {rel: load(rel, problems) for rel in MANIFESTS}

    pins: list[tuple[str, str]] = []
    pins += grep("VERSION", r"^\s*(\S+)\s*$", problems)
    pins += grep("bin/rbt", r'^REBOOT_VERSION="([^"]+)"', problems)
    for pyproject in sorted(ROOT.glob("skills/build/templates/*/pyproject.toml")):
        pins += grep(str(pyproject.relative_to(ROOT)), r'"reboot(?:\[dev\])?==([^"]+)"', problems)

    codex = docs.get(".codex-plugin/plugin.json")
    if codex is not None:
        pins.append((".codex-plugin/plugin.json: version", str(codex.get("version"))))

    market = docs.get(".claude-plugin/marketplace.json")
    if market is not None:
        pins.append((".claude-plugin/marketplace.json: metadata.version",
                     str((market.get("metadata") or {}).get("version"))))
        problems += claude_entry_problems(market)
    codex_market = docs.get(".agents/plugins/marketplace.json")
    if market is not None and codex_market is not None:
        problems += codex_marketplace_problems(codex_market, market)

    versions = {v for _, v in pins}
    if len(versions) > 1:
        problems.append("the Reboot version pins disagree:")
        problems += [f"  {where}: {v}" for where, v in pins]

    # Envoy: the plugin's installer and the templates' CI workflow fetch
    # the same release (Reboot's own ENVOY_VERSION).
    envoy = grep("lib/install_envoy.sh", r'^ENVOY_VERSION="([^"]+)"', problems)
    envoy_sum = grep("lib/install_envoy.sh", r'^SHA256_LINUX_X64="([0-9a-f]+)"', problems)
    for workflow in sorted(ROOT.glob("skills/build/templates/*/.github/workflows/prove.yml")):
        rel = str(workflow.relative_to(ROOT))
        envoy += grep(rel, r"envoy-([0-9.]+)-linux-x86_64$", problems)
        envoy_sum += grep(rel, r'^\s*echo "([0-9a-f]{64})  ', problems)
    for label, found in (("Envoy version", envoy), ("Envoy SHA-256", envoy_sum)):
        if len({v for _, v in found}) > 1:
            problems.append(f"the {label} pins disagree:")
            problems += [f"  {where}: {v}" for where, v in found]

    for p in problems:
        print(p, file=sys.stderr)
    if not problems:
        print(f"manifests OK; {len(pins)} pins at {versions.pop()}, Envoy {envoy[0][1]}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
