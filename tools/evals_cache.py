#!/usr/bin/env python3
"""The eval result cache and the per-grader spread report, for
`tools/run-evals.sh`.

A case's key hashes what can change its result: every file in its
directory (prompt.md, case.yaml, graders, fixture), every skill its
`tool: Skill` graders name (SKILL.md and references/; python's with
build's, which reads them), hooks-handlers/remind.sh, the templates'
AGENTS.md, and the flags that change a score (runs, ablation, judge
model, model, scaffold, mocks, allowed tools). A result directory
under evals/results/ holds `cache-keys.json`, {case: key}, for the
cases it ran cleanly; a later run with the same key prints that result
instead of running.

    evals_cache.py plan RESULTS -- <run-evals flags>    # "cached CASE DIR" / "run CASE KEY" lines
    evals_cache.py filters -- <flags>                   # the flags less --case/--tag, one per line
    evals_cache.py store RESULTS_DIR CASE=KEY...        # after a run: write cache-keys.json
    evals_cache.py show RESULT_DIR [CASE...]            # scores and the spread; exit 1 under --threshold
"""

from __future__ import annotations

import fnmatch
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYS = "cache-keys.json"

_spec = importlib.util.spec_from_file_location("check", ROOT / "tools" / "check.py")
check = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("check", check)
_spec.loader.exec_module(check)

# Flags that take a value (or several, until the next flag).
VALUED = {"--ablation", "--case", "-j", "--concurrency", "--eval-dir", "--judge-model",
          "--max-cost-usd", "--mocks", "--model", "--output-dir", "--report", "--runs",
          "--threshold"}
VARIADIC = {"--tag", "--allow-tools"}
# The ones that change what a case scores.
RESULT_FLAGS = ["--runs", "--ablation", "--judge-model", "--model", "--scaffold", "--no-scaffold",
                "--mocks", "--allow-tools", "--eval-dir"]


def parse(args: list) -> dict:
    """{flag: [values]} (a bare flag maps to [])."""
    out: dict = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and "=" in a:
            flag, value = a.split("=", 1)
            out.setdefault(flag, []).append(value)
        elif a in VALUED and i + 1 < len(args):
            i += 1
            out.setdefault(a, []).append(args[i])
        elif a in VARIADIC:
            vals = out.setdefault(a, [])
            while i + 1 < len(args) and not args[i + 1].startswith("-"):
                i += 1
                vals.append(args[i])
        else:
            out.setdefault(a, [])
        i += 1
    return out


def without_filters(args: list) -> list:
    """`args` less --case and --tag (each with its values)."""
    out, i = [], 0
    while i < len(args):
        a = args[i]
        if a.startswith("--case=") or a.startswith("--tag="):
            pass
        elif a == "--case":
            i += 1
        elif a == "--tag":
            while i + 1 < len(args) and not args[i + 1].startswith("-"):
                i += 1
        else:
            out.append(a)
        i += 1
    return out


def selected(args: list, evals: Path) -> list:
    """The cases `claude plugin eval` runs for these flags: --case glob, --tag."""
    flags = parse(args)
    pattern = (flags.get("--case") or [None])[-1]
    tags = set(flags.get("--tag") or [])
    names = []
    for case in sorted(p for p in evals.iterdir() if p.is_dir() and p.name != "results"):
        if not ((case / "prompt.md").exists() or (case / "case.yaml").exists()):
            continue
        if pattern and not fnmatch.fnmatch(case.name, pattern):
            continue
        if tags:
            text = ""
            for f in ("case.yaml", "prompt.md"):
                if (case / f).exists():
                    text += (case / f).read_text()
            m = re.search(r"^tags:\s*\[(.*)\]", text, re.M)
            found = {t.strip().strip("'\"") for t in m.group(1).split(",")} if m else set()
            if not tags & found:
                continue
        names.append(case.name)
    return names


def skills_for(case: str, root: Path) -> list:
    """The skill directories a case can load, by its Skill graders."""
    pats = check.eval_cases(root).get(case, [])
    hits = []
    for skill in sorted(p.name for p in (root / "skills").iterdir() if p.is_dir()):
        probes = [f'"skill": "{skill}"', f'"skill": "reboot:{skill}"']
        if any(re.search(p, probe) for p in pats for probe in probes):
            hits.append(skill)
    for reader, read in ((v, k) for k, v in check.READ_BY.items()):
        if reader in hits and read not in hits:
            hits.append(read)
    return sorted(hits)


def files_for(case: str, root: Path) -> list:
    files = [p for p in (root / "evals" / case).rglob("*") if p.is_file()]
    for skill in skills_for(case, root):
        d = root / "skills" / skill
        files += [d / "SKILL.md"] if (d / "SKILL.md").exists() else []
        files += [p for p in (d / "references").rglob("*") if p.is_file()]
    files += [root / "hooks-handlers" / "remind.sh"]
    files += sorted((root / "skills" / "build" / "templates").glob("*/AGENTS.md"))
    return sorted({p for p in files if p.exists() and "__pycache__" not in p.parts})


def key_for(case: str, args: list, root: Path = ROOT) -> str:
    h = hashlib.sha256()
    for p in files_for(case, root):
        h.update(str(p.relative_to(root)).encode() + b"\0")
        h.update(p.read_bytes() + b"\0")
    flags = parse(args)
    for flag in RESULT_FLAGS:
        if flag in flags:
            h.update(f"{flag}={','.join(sorted(flags[flag]))}\0".encode())
    return h.hexdigest()[:16]


def lookup(results: Path, case: str, key: str):
    """The newest result directory that ran `case` under `key`, or None."""
    if not results.is_dir():
        return None
    for d in sorted((p for p in results.iterdir() if p.is_dir()), reverse=True):
        try:
            keys = json.loads((d / KEYS).read_text())
        except (OSError, ValueError):
            continue
        if keys.get(case) == key and (d / "aggregate-result.json").exists():
            return d
    return None


def clean_cases(result: dict) -> set:
    """Cases whose every run finished without an error."""
    if result.get("partial"):
        return set()
    ok = set()
    for case in result.get("cases", []):
        runs = [r for arm in case.get("arms", {}).values() for r in arm]
        if runs and not any(r.get("error") for r in runs):
            ok.add(case["name"])
    return ok


def votes(grader: dict) -> str:
    if grader.get("judgeVotes"):
        return "".join("P" if v else "F" for v in grader["judgeVotes"])
    return "P" if grader.get("passed") else "F"


def spread(case: dict) -> list:
    """Lines: each arm's per-run scores, then each grader's votes per run."""
    lines = []
    for arm, runs in case.get("arms", {}).items():
        if not runs:
            continue
        scores = [r.get("score") or 0.0 for r in runs]
        rng = max(scores) - min(scores)
        lines.append(f"  {arm}: {len(runs)} run(s), score per run "
                     f"{' '.join(f'{s:.2f}' for s in scores)}; mean {sum(scores) / len(scores):.2f}, "
                     f"range {rng:.2f}")
        names = [g["name"] for g in runs[0].get("graders", [])]
        width = max((len(n) for n in names), default=0)
        for name in names:
            per_run, passes, total, run_passes = [], 0, 0, 0
            for r in runs:
                g = next((g for g in r.get("graders", []) if g["name"] == name), None)
                if g is None:
                    per_run.append("-")
                    continue
                v = votes(g)
                per_run.append(v)
                passes += v.count("P")
                total += len(v)
                run_passes += bool(g.get("passed"))
            g0 = next(g for g in runs[0]["graders"] if g["name"] == name)
            note = "" if g0.get("scored", True) else "  (not scored)"
            lines.append(f"    {name:<{width}}  {' '.join(per_run)}   {passes}/{total} votes, "
                         f"{run_passes}/{len(runs)} runs{note}")
        if len(runs) > 1:
            lines.append(f"    single runs of this case differ by up to {rng:.2f} on their own: "
                         f"a gap between two scores smaller than that is likely noise")
    return lines


def show(result_dir: Path, cases: list, threshold: float, cached: bool) -> int:
    result = json.loads((result_dir / "aggregate-result.json").read_text())
    suite = result.get("suite", {})
    status = 0
    for case in result.get("cases", []):
        if cases and case["name"] not in cases:
            continue
        score = (case.get("aggregates") or {}).get("score")
        head = "cached" if cached else "result"
        where = result_dir.relative_to(ROOT) if result_dir.is_relative_to(ROOT) else result_dir
        print(f"{head}: {case['name']} score {score if score is None else f'{score:.2f}'} "
              f"(judge {suite.get('judgeModel')}, ablation {suite.get('ablation')}) {where}")
        for line in spread(case):
            print(line)
        if score is not None and score < threshold:
            status = 1
    return status


def main(argv: list) -> int:
    cmd, rest = argv[0], argv[1:]
    if cmd == "plan":
        results, args = Path(rest[0]), rest[rest.index("--") + 1:]
        for case in selected(args, ROOT / "evals"):
            key = key_for(case, args)
            hit = None if "--fresh" in args else lookup(results, case, key)
            print(f"cached {case} {hit}" if hit else f"run {case} {key}")
        return 0
    if cmd == "filters":
        for a in without_filters(rest[rest.index("--") + 1:]):
            print(a)
        return 0
    if cmd == "store":
        d = Path(rest[0])
        result = json.loads((d / "aggregate-result.json").read_text())
        ran = {c["name"] for c in result.get("cases", [])}
        ok = clean_cases(result)
        keys = {}
        for pair in rest[1:]:
            case, key = pair.split("=", 1)
            if case in ran and case in ok:
                keys[case] = key
        if keys:
            (d / KEYS).write_text(json.dumps(keys, indent=1, sort_keys=True) + "\n")
        return 0
    if cmd == "show":
        d = Path(rest[0])
        args = rest[rest.index("--") + 1:] if "--" in rest else []
        cases = rest[1:rest.index("--")] if "--" in rest else rest[1:]
        threshold = float((parse(args).get("--threshold") or ["1.0"])[-1])
        return show(d, cases, threshold, cached="--cached" in args)
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
