#!/usr/bin/env python3
"""Check the plugin's manifests parse and its version pins agree.

Every JSON manifest the two agents read must parse. The plugin's
version is the Reboot version it pins (`bin/rbt`): a user who installs
a new plugin version gets that Reboot, and the templates must scaffold
onto the same one. Nothing else enforces that these say the same
thing, so this does:

* `VERSION`
* `.claude-plugin/marketplace.json` (`metadata.version`, and the
  `reboot` entry's `version` if it has one)
* `.codex-plugin/plugin.json`
* `bin/rbt` (`REBOOT_VERSION=`)
* `skills/build/templates/*/pyproject.toml` (`reboot==`, `reboot[dev]==`)

A marketplace entry with a local `source` and a `version` must also
agree with that plugin's own `plugin.json` (the mods).

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
        for entry in market.get("plugins", []):
            name = entry.get("name")
            if name == "reboot" and "version" in entry:
                pins.append((f".claude-plugin/marketplace.json: plugins[{name}].version",
                             str(entry["version"])))
            source = entry.get("source")
            if "version" in entry and isinstance(source, str):
                own = ROOT / source / ".claude-plugin" / "plugin.json"
                if own.is_file():
                    try:
                        own_version = json.loads(own.read_text(encoding="utf-8")).get("version")
                    except json.JSONDecodeError:
                        own_version = None  # reported above if it is a listed manifest
                    if own_version != entry["version"]:
                        problems.append(
                            f".claude-plugin/marketplace.json: {name} is {entry['version']}, "
                            f"{own.relative_to(ROOT)} says {own_version}")

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
