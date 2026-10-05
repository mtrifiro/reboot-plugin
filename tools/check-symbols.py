#!/usr/bin/env python3
"""Check every `reboot` symbol the skills name against the pinned package.

Extracts, from every SKILL.md and reference:

* `from reboot… import A, B` and `import reboot…` lines in code blocks,
* dotted `reboot.x.y.Z` names in inline code,
* `Name.method(` calls where `Name` was imported from `reboot…` in the
  same file (e.g. `OrderedMap.ref(`, `Queue.create(`),

then imports each one inside an isolated environment holding exactly
the Reboot version `bin/rbt` pins (with the extras the skills
recommend), and reports every name that does not resolve.

Usage:
    tools/check-symbols.py          # report; exit 1 on any unresolved symbol
    tools/check-symbols.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
UV = ROOT / "bin" / "uv"

EXTRAS = "anthropic,dev"
PYTHON = "3.12"

FENCE = re.compile(r"^\s*(```+|~~~+)")
FROM_IMPORT = re.compile(r"^\s*from\s+(reboot(?:\.\w+)*)\s+import\s+(.+)$")
IMPORT = re.compile(r"^\s*import\s+(reboot(?:\.\w+)*)")
INLINE_DOTTED = re.compile(r"`(reboot(?:\.\w+)+)`")
INCORRECT = re.compile(r"incorrect|don'?t|never|wrong|\bbad\b|avoid|removed|before:?\s*$", re.IGNORECASE)

CHECKER = r"""
import importlib, json, sys

def load(module):
    # Return (object, remaining attrs) for the longest importable prefix.
    parts = module.split(".")
    for i in range(len(parts), 0, -1):
        try:
            return importlib.import_module(".".join(parts[:i])), parts[i:], None
        except ModuleNotFoundError as e:
            missing = e.name
            if missing and not module.startswith(missing):
                return None, [], f"missing dependency {missing!r} importing {module}"
        except Exception as e:
            return None, [], f"{type(e).__name__} importing {module}: {e}"
    return None, [], f"ModuleNotFoundError: {module}"

out = []
for item in json.load(sys.stdin):
    obj, rest, error = load(item["module"])
    if error:
        out.append({**item, "error": error})
        continue
    path = obj.__name__
    for attr in rest + item["attrs"]:
        if not hasattr(obj, attr):
            try:  # a submodule not yet imported by its package
                obj = importlib.import_module(f"{path}.{attr}")
                path += "." + attr
                continue
            except Exception:
                pass
            out.append({**item, "error": f"{path} has no attribute {attr!r}"})
            break
        obj = getattr(obj, attr)
        path += "." + attr
json.dump(out, sys.stdout)
"""


def reboot_version() -> str:
    m = re.search(r'REBOOT_VERSION="([^"]+)"', (ROOT / "bin" / "rbt").read_text())
    if not m:
        sys.exit("could not find REBOOT_VERSION in bin/rbt")
    return m.group(1)


def names(clause: str) -> list[str]:
    clause = clause.split("#", 1)[0].strip().strip("()").rstrip("\\")
    out = []
    for part in clause.split(","):
        name = part.strip().split(" as ")[0].strip()
        if re.fullmatch(r"[A-Za-z_]\w*", name):
            out.append(name)
    return out


def extract(path: Path) -> list[dict]:
    rel = str(path.relative_to(ROOT))
    lines = path.read_text(encoding="utf-8").splitlines()
    items: list[dict] = []
    imported: dict[str, str] = {}  # local name -> module
    in_block = False
    incorrect = False
    continuation: tuple[str, int] | None = None
    call_sites: list[tuple[int, str, str, bool]] = []

    for i, line in enumerate(lines, start=1):
        if FENCE.match(line):
            if not in_block:
                incorrect = bool(INCORRECT.search(" ".join(lines[max(0, i - 4) : i - 1])))
            in_block = not in_block
            continue
        if in_block:
            if continuation:
                module, start = continuation
                for name in names(line):
                    imported[name] = module
                    items.append(dict(file=rel, line=start, module=module, attrs=[name],
                                      incorrect=incorrect))
                if ")" in line:
                    continuation = None
                continue
            m = FROM_IMPORT.match(line)
            if m:
                module, clause = m.groups()
                if clause.strip().startswith("(") and ")" not in clause:
                    continuation = (module, i)
                for name in names(clause):
                    imported[name] = module
                    items.append(dict(file=rel, line=i, module=module, attrs=[name],
                                      incorrect=incorrect))
                continue
            m = IMPORT.match(line)
            if m:
                items.append(dict(file=rel, line=i, module=m.group(1), attrs=[],
                                  incorrect=incorrect))
                continue
            for cm in re.finditer(r"\b([A-Z]\w+)\.([a-z_]\w*)\(", line):
                call_sites.append((i, cm.group(1), cm.group(2), incorrect))
        else:
            for m in INLINE_DOTTED.finditer(line):
                items.append(dict(file=rel, line=i, module=m.group(1), attrs=[],
                                  incorrect=bool(INCORRECT.search(line))))

    for lineno, cls, method, bad in call_sites:
        if cls in imported:
            items.append(dict(file=rel, line=lineno, module=imported[cls],
                              attrs=[cls, method], incorrect=bad))
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    items = [item for p in sorted(SKILLS.rglob("*.md")) for item in extract(p)]

    # Check each distinct (module, attrs) once, then map back to sites.
    distinct = {(i["module"], tuple(i["attrs"])) for i in items}
    payload = [{"module": m, "attrs": list(a)} for m, a in sorted(distinct)]
    version = reboot_version()
    result = subprocess.run(
        [str(UV), "run", "--no-project", "--quiet", f"--python={PYTHON}",
         f"--with=reboot[{EXTRAS}]=={version}",
         # reboot.bdd.web imports playwright, which the extras don't pull in.
         "--with=playwright", "python", "-c", CHECKER],
        input=json.dumps(payload), capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return 2
    errors = {(e["module"], tuple(e["attrs"])): e["error"] for e in json.loads(result.stdout)}

    sites: dict[tuple, list[dict]] = defaultdict(list)
    for item in items:
        key = (item["module"], tuple(item["attrs"]))
        if key in errors:
            sites[key].append(item)

    real = {k: v for k, v in sites.items() if not all(s["incorrect"] for s in v)}

    if args.json:
        print(json.dumps([
            {"symbol": ".".join([k[0], *k[1]]), "error": errors[k],
             "sites": [f"{s['file']}:{s['line']}" for s in v],
             "incorrect_example_only": k not in real}
            for k, v in sites.items()
        ], indent=2))
    else:
        for key, where in sorted(real.items()):
            print(f"{'.'.join([key[0], *key[1]])}: {errors[key]}")
            for s in where:
                print(f"    {s['file']}:{s['line']}")
        print(f"\nreboot=={version}: checked {len(distinct)} distinct symbols "
              f"from {len(items)} mentions; {len(real)} unresolved")
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main())
