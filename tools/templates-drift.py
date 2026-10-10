#!/usr/bin/env python3
"""Keep the scaffold templates' shared files identical.

`skills/build/templates/{mcp-ui,web-app,both}` carry copies of the same
scripts, configs and tests. A fix made in one must reach the others,
and nothing but this check notices when it doesn't. The rule: a path
that exists in two or more templates is byte-identical in all of them,
except the files that differ by design, listed in DIFFERS with the
reason. An entry whose copies have become identical is reported too,
so the list stays honest. PAIRS names files that live at different
paths and must still match (the web app's files under `web-app/web/`
and `both/frontend/web/`).

The stylesheets follow their own rule (`style-check.py`: the web sheet
is the source and the MCP sheet adds `.ui`), so here they differ by
design.

Usage:
    tools/templates-drift.py                 # exit 1 on drift
    tools/templates-drift.py --sync mcp-ui   # copy that template's shared files over the others'
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "skills" / "build" / "templates"
NAMES = ("mcp-ui", "web-app", "both")

# Build products and generated code a developer may have left in a
# template after running it in place; git ignores them too.
SKIP_DIRS = {"node_modules", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache",
             "dist", ".reboot", ".rbt", "screenshots", "exports"}
SKIP_FILES = {".DS_Store"}
GENERATED = ("backend/api/", "frontend/api/", "web/src/api/")

# Shared paths that differ by design, with the reason.
DIFFERS = {
    ".gitignore": "the generated-code paths follow .rbtrc; only the web front doors make screenshots/",
    ".rbtrc": "codegen paths, the frontend configs and `serve run` differ per front door",
    "AGENTS.md": "each front door's own instructions",
    "api/__app__/v1/__app__.py": "the sample API",
    "backend/src/main.py": "the sample application",
    "backend/src/servicers/__app__.py": "the sample servicer",
    "backend/src/servicers/registry.py": "registers the sample servicer",
    "deploy/config": "the web front doors publish a site",
    "frontend/mcp/styles.css": "style-check.py: both's imports the shared sheet",
    "frontend/package.json": "both adds the web app's fonts",
    "frontend/vite-env.d.ts": "both declares the deploy-time env",
    "scripts/page_timing.py": "where the web app's build is served",
    "scripts/screenshots.py": "where the web app is served",
    "tests/backup_restore_test.py": "the sample state type",
    "tests/conftest.py": "the sample app's fixtures",
    "tests/counting.feature": "the sample scenarios",
}

# Files at different paths that must match.
PAIRS = [
    ("web-app/web/src/nav.tsx", "both/frontend/web/src/nav.tsx"),
    ("web-app/web/src/theme.tsx", "both/frontend/web/src/theme.tsx"),
    ("web-app/web/.env.development", "both/frontend/web/.env.development"),
]


def files_of(name: str) -> dict[str, Path]:
    base = TEMPLATES / name
    out = {}
    for path in base.rglob("*"):
        if not path.is_file() or path.name in SKIP_FILES:
            continue
        rel = path.relative_to(base)
        if SKIP_DIRS.intersection(rel.parts):
            continue
        posix = rel.as_posix()
        if posix.startswith(GENERATED):
            continue
        out[posix] = path
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--sync", metavar="TEMPLATE", choices=NAMES,
                        help="copy this template's shared files over the other templates'")
    args = parser.parse_args()

    files = {name: files_of(name) for name in NAMES}
    shared = sorted({rel for name in NAMES for rel in files[name]
                     if sum(rel in files[n] for n in NAMES) > 1})
    pairs = [(TEMPLATES / a, TEMPLATES / b) for a, b in PAIRS]

    if args.sync:
        source = args.sync
        copied = 0
        for rel in shared:
            if rel in DIFFERS or rel not in files[source]:
                continue
            data = files[source][rel].read_bytes()
            for name in NAMES:
                if name != source and rel in files[name] and files[name][rel].read_bytes() != data:
                    files[name][rel].write_bytes(data)
                    copied += 1
        for a, b in pairs:
            src, dst = (a, b) if a.relative_to(TEMPLATES).parts[0] == source else (b, a)
            if src.relative_to(TEMPLATES).parts[0] == source and src.is_file() and dst.is_file() \
                    and src.read_bytes() != dst.read_bytes():
                dst.write_bytes(src.read_bytes())
                copied += 1
        print(f"synced {copied} file(s) from {source}")

    problems = []
    for rel in shared:
        holders = [name for name in NAMES if rel in files[name]]
        contents = {name: files[name][rel].read_bytes() for name in holders}
        same = len(set(contents.values())) == 1
        if rel in DIFFERS:
            if same:
                problems.append(f"{rel}: listed in DIFFERS but identical in {', '.join(holders)}; drop the entry")
        elif not same:
            problems.append(f"{rel}: differs between {' and '.join(holders)} (--sync <template> to propagate one)")
    for rel in DIFFERS:
        if sum(rel in files[n] for n in NAMES) < 2:
            problems.append(f"{rel}: listed in DIFFERS but not shared; drop the entry")
    for a, b in pairs:
        if not (a.is_file() and b.is_file()):
            problems.append(f"{a.relative_to(TEMPLATES)} / {b.relative_to(TEMPLATES)}: a paired file is missing")
        elif a.read_bytes() != b.read_bytes():
            problems.append(f"{a.relative_to(TEMPLATES)} differs from {b.relative_to(TEMPLATES)}")

    for p in problems:
        print(p, file=sys.stderr)
    if not problems:
        print(f"templates agree: {len(shared) - len(DIFFERS)} shared files identical, "
              f"{len(DIFFERS)} differ by design, {len(pairs)} pairs match")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
