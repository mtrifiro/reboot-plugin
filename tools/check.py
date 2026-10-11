#!/usr/bin/env python3
"""The plugin's own checks, in stages ordered by time and by what they
protect, and a selector that runs only what a change can break.

    tools/check.sh                      # lint, shell, unit (= check-all.sh)
    tools/check.sh --upto integration   # and the integration stage (= check-all.sh --full)
    tools/check.sh --stage unit         # one stage (repeatable)
    tools/check.sh --changed            # what the paths changed since the merge base
                                        # with main can break (lint always runs whole)
    tools/check.sh --changed HEAD       # the same for uncommitted work only
    tools/check.sh --only shellcheck    # named checks (repeatable)
    tools/check.sh --list               # stages, checks, measured times
    tools/check.sh --changed --explain  # which row of PATHS picked each check
    tools/check.sh --run-evals          # behavior: run the eval cases (model calls, money)

A stage runs all its checks, prints each one's time and the stage's,
and the run stops after the first stage with a failure. Output of a
check is shown when it fails (`-v` shows it always). The behavior
stage only prints the eval cases and the `tools/run-evals.sh` command
unless `--run-evals` is given.

STAGES, CHECKS and PATHS below are the whole configuration.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (name, what it protects). Seconds are measured on a 2026 Mac with the
# downloads cached (2026-10-11); the first integration run fetches the
# pinned Reboot, Node, pytest and Chromium.
STAGES = [
    ("lint", "static checks over the text: generated regions, front matter, findings, budget, style copies, manifests"),
    ("shell", "shellcheck over every shell script"),
    ("unit", "the unittest files: hooks, shims, template scripts, tools, against fakes and temp dirs"),
    ("integration", "against the pinned Reboot and real downloads: every rbt flag and reboot symbol, the templates built and their scenarios run, the rendered style page, the mods"),
    ("behavior", "what a fresh agent decides with the skills (evals): model calls, costs money, opt-in"),
]
STAGE_NAMES = [s for s, _ in STAGES]

SHELL_FILES = [
    "install.sh", "hooks/*.sh", "hooks-handlers/*.sh", "lib/*.sh", "bin/*", "tools/*.sh",
    "skills/build/templates/copy.sh", "skills/build/templates/*/scripts/*.sh",
    "skills/build/templates/*/deploy/before-backend", "skills/build/templates/*/.githooks/*",
]
SHELLCHECK_PY = ["bin/uvx", "--from", "shellcheck-py==0.11.0.1", "shellcheck"]
PYTEST = ["bin/uv", "run", "--no-project", "--with", "pytest==8.4.2"]
PYTEST_BDD = PYTEST + ["--with", "pytest-bdd==8.1.0"]


@dataclass
class Check:
    name: str
    stage: str
    cmd: list
    seconds: float              # measured
    file: str = ""              # the test file it runs, for PATHS' @self
    env: dict = field(default_factory=dict)
    needs: str = ""             # a command that must be on PATH, else skipped


def unit(path: str, seconds: float) -> Check:
    name = path[len("tests/"):-len("_test.py")]
    return Check(name, "unit", ["python3", path, "-q"], seconds, file=path)


def pytest_unit(path: str, seconds: float, bdd: bool = False) -> Check:
    name = "pytest:" + Path(path).name[:-len("_test.py")]
    return Check(name, "integration", (PYTEST_BDD if bdd else PYTEST) + ["python", path, "-q"],
                 seconds, file=path)


CHECKS = [
    Check("gen-index", "lint", ["python3", "tools/gen-index.py", "--check", "--quiet"], 0.09),
    Check("lint-references", "lint", ["python3", "tools/lint-references.py"], 0.05),
    Check("lint-frontmatter", "lint", ["python3", "tools/lint-frontmatter.py"], 0.15),
    Check("findings", "lint", ["python3", "tools/findings.py", "--check"], 0.09),
    Check("budget", "lint", ["python3", "tools/budget.py", "--check"], 0.05),
    Check("style", "lint", ["python3", "tools/style-check.py"], 0.03),
    Check("templates-drift", "lint", ["python3", "tools/templates-drift.py"], 0.06),
    Check("manifests", "lint", ["python3", "tools/check-manifests.py"], 0.02),

    Check("shellcheck", "shell", [], 1.1),

    unit("tests/hooks/auto_approve_test.py", 1.6),
    unit("tests/hooks/orphans_test.py", 9.7),
    unit("tests/hooks/schema_guard_test.py", 6.1),   # skips itself without a cached Node
    unit("tests/hooks/suite_guard_test.py", 1.1),
    unit("tests/hooks/session_start_test.py", 0.7),
    unit("tests/hooks/remind_test.py", 0.3),
    unit("tests/shims/rbt_test.py", 8.3),
    unit("tests/shims/uv_test.py", 4.8),
    unit("tests/templates/copy_test.py", 1.9),
    unit("tests/templates/run_progress_test.py", 0.04),   # skips itself without pytest
    unit("tests/templates/step_order_test.py", 0.04),     # skips itself without pytest-bdd
    unit("tests/templates/ports_test.py", 4.9),
    unit("tests/templates/test_sh_test.py", 0.04),        # skips itself without pytest
    unit("tests/templates/feature_lint_test.py", 0.04),   # skips itself without pytest-bdd
    unit("tests/templates/harness_hygiene_test.py", 0.04),
    unit("tests/templates/api_lint_test.py", 0.4),
    unit("tests/templates/doctor_test.py", 0.6),
    unit("tests/templates/placeholder_test.py", 7.2),
    unit("tests/templates/deploy_test.py", 0.1),
    unit("tests/tools/gen_index_test.py", 0.1),
    unit("tests/tools/findings_test.py", 0.2),
    unit("tests/tools/lint_frontmatter_test.py", 0.2),
    unit("tests/tools/check_manifests_test.py", 0.1),
    unit("tests/tools/check_cli_test.py", 0.04),
    unit("tests/tools/check_symbols_test.py", 0.04),
    unit("tests/tools/run_evals_test.py", 3.6),
    unit("tests/tools/check_test.py", 0.5),

    Check("check-cli", "integration", ["python3", "tools/check-cli.py"], 18.3),
    Check("check-symbols", "integration", ["python3", "tools/check-symbols.py"], 1.6),
    Check("schema-guard-node", "integration", ["python3", "tests/hooks/schema_guard_test.py", "-q"],
          6.2, file="tests/hooks/schema_guard_test.py", env={"REBOOT_FETCH_NODE": "1"}),
    pytest_unit("tests/templates/run_progress_test.py", 1.0),
    pytest_unit("tests/templates/test_sh_test.py", 2.2),
    pytest_unit("tests/templates/feature_lint_test.py", 0.9, bdd=True),
    pytest_unit("tests/templates/step_order_test.py", 0.5, bdd=True),
    Check("style-browser", "integration",
          ["bin/uv", "run", "--no-project", "--with", "playwright", "sh", "-c",
           "python -m playwright install --with-deps chromium >/dev/null && python tools/style-check.py --browser"],
          1.0),
    Check("templates-smoke", "integration", ["tools/templates-smoke.sh"], 195.0, env={"SMOKE_FULL": "1"}),
    Check("mods", "integration", ["tools/check-mods.sh"], 3.2, needs="claude"),
]
BY_NAME = {c.name: c for c in CHECKS}

GROUPS = {
    "hook-tests": [c.name for c in CHECKS if c.name.startswith("hooks/")],
    "shim-tests": [c.name for c in CHECKS if c.name.startswith("shims/")],
    "template-tests": [c.name for c in CHECKS if c.name.startswith("templates/")],
    "template-pytest": [c.name for c in CHECKS if c.name.startswith("pytest:")],
}

# Path -> checks, beyond the lint stage, which runs whole on any change
# (under a second, and its checks read across the tree: a renamed
# heading breaks findings, a reference breaks gen-index). The first row
# whose glob matches a path wins (fnmatch: `*` crosses `/`), so specific
# rows come first. A token is a check, `@group`, `@self` (the check that
# runs this test file), `evals` (the cases that load the changed skill,
# or the changed case) or `evals:all`. A path no row matches runs the
# shell and unit stages whole.
PATHS = [
    # The templates: copied into every user's project.
    ("skills/build/templates/*.md", ["@template-tests", "check-cli", "check-symbols", "templates-smoke"]),
    ("skills/build/templates/*", ["shellcheck", "@template-tests", "@template-pytest",
                                  "style-browser", "templates-smoke"]),
    # The vendored package the uv shim installs.
    ("skills/python/vendor/*", ["shims/uv", "templates-smoke"]),
    # Skill text: what an agent reads. check-cli/symbols scan skills/**/*.md.
    ("skills/*", ["check-cli", "check-symbols", "evals"]),
    # Hooks: run in every session.
    ("hooks/schema-guard*", ["hooks/schema_guard", "schema-guard-node", "shellcheck"]),
    ("hooks-handlers/remind.sh", ["@hook-tests", "shellcheck", "evals:all"]),
    ("hooks/*", ["@hook-tests", "shellcheck"]),
    ("hooks-handlers/*", ["@hook-tests", "shellcheck"]),
    # Shims and their helpers: every rbt/uv/node call goes through them.
    ("bin/*", ["@shim-tests", "hooks/session_start", "shellcheck", "check-cli", "check-symbols",
               "schema-guard-node", "templates-smoke"]),
    ("lib/*", ["@shim-tests", "hooks/orphans", "hooks/schema_guard", "shellcheck",
               "check-symbols", "schema-guard-node", "templates-smoke"]),
    ("install.sh", ["shellcheck"]),
    ("VERSION", ["@shim-tests", "tools/check_manifests", "check-cli", "check-symbols", "templates-smoke"]),
    (".claude-plugin/*", ["tools/check_manifests"]),
    (".codex-plugin/*", ["tools/check_manifests"]),
    (".agents/plugins/*", ["tools/check_manifests"]),
    (".agents/skills/*", ["check-cli", "check-symbols", "evals"]),
    # The tools: each with its own test.
    ("tools/gen-index.py", ["tools/gen_index"]),
    ("tools/findings.py", ["tools/findings"]),
    ("tools/lint-frontmatter.py", ["tools/lint_frontmatter"]),
    ("tools/reflib.py", ["tools/gen_index", "tools/findings", "tools/lint_frontmatter"]),
    ("tools/check-manifests.py", ["tools/check_manifests"]),
    ("tools/check-cli.py", ["tools/check_cli", "check-cli"]),
    ("tools/check-symbols.py", ["tools/check_symbols", "check-symbols"]),
    ("tools/known-defects.json", ["check-symbols"]),
    ("tools/run-evals.sh", ["tools/run_evals", "shellcheck"]),
    ("tools/style-check.*", ["style-browser"]),
    ("tools/templates-smoke.sh", ["shellcheck", "templates-smoke"]),
    ("tools/check-mods.sh", ["shellcheck", "mods"]),
    ("tools/check.py", ["tools/check"]),
    ("tools/*.sh", ["shellcheck", "tools/check"]),
    ("tools/*", []),
    # A test runs itself.
    ("tests/*_test.py", ["@self"]),
    ("tests/*", []),
    ("mods/*", ["mods"]),
    ("evals/README.md", []),
    ("evals/*", ["tools/run_evals", "evals"]),
    # Text the lint stage covers.
    ("findings/*", []),
    ("docs/*", []),
    (".github/*", []),
    ("*.md", []),
    (".gitignore", []),
    ("BUILD.bazel", []),
    ("*/BUILD.bazel", []),
]

# A skill whose text another skill reads in the design phase is covered
# by the cases that load the reader: build points at python/references/.
READ_BY = {"python": "build"}


# --- selection -------------------------------------------------------

def row_for(path: str):
    for glob, tokens in PATHS:
        if fnmatch.fnmatchcase(path, glob):
            return glob, tokens
    return None, None


def eval_cases(root: Path = ROOT) -> dict:
    """Case -> the skill-name regexes its `tool_used: Skill` graders match."""
    cases = {}
    for case in sorted(p for p in (root / "evals").iterdir() if p.is_dir() and p.name != "results"):
        pats = []
        for grader in sorted((case / "graders").glob("*.md")):
            text = grader.read_text()
            if not re.search(r"^tool:\s*Skill\s*$", text, re.M):
                continue
            m = re.search(r"^input_match:\s*'(.*)'\s*$", text, re.M)
            if m:
                pats.append(m.group(1))
        cases[case.name] = pats
    return cases


def cases_for_skill(skill: str, cases: dict) -> list:
    names = {skill, READ_BY.get(skill, skill)}
    hits = []
    for case, pats in cases.items():
        probes = [f'"skill": "{n}"' for n in names] + [f'"skill": "reboot:{n}"' for n in names]
        if any(re.search(p, probe) for p in pats for probe in probes):
            hits.append(case)
    return hits


@dataclass
class Selection:
    checks: set
    cases: set
    all_cases: bool
    unmapped: list
    why: dict          # path -> (glob or None, [check names])


def select(paths: list, cases: dict | None = None) -> Selection:
    """The checks and eval cases the changed `paths` can break."""
    if cases is None:
        cases = eval_cases()
    by_file = {}
    for c in CHECKS:
        if c.file:
            by_file.setdefault(c.file, []).append(c.name)
    sel = Selection(set(), set(), False, [], {})
    for path in paths:
        glob, tokens = row_for(path)
        picked = []
        if glob is None:
            sel.unmapped.append(path)
            picked = [c.name for c in CHECKS if c.stage in ("shell", "unit")]
        for tok in tokens or []:
            if tok.startswith("@") and tok != "@self":
                picked += GROUPS[tok[1:]]
            elif tok == "@self":
                picked += by_file.get(path, [])
            elif tok == "evals:all":
                sel.all_cases = True
            elif tok == "evals":
                parts = path.split("/")
                if parts[0] == "evals" and len(parts) > 2 and parts[1] in cases:
                    sel.cases.add(parts[1])
                elif parts[0] in ("skills", ".agents") and len(parts) > 2:
                    sel.cases.update(cases_for_skill(skill_of(path), cases))
            else:
                if tok not in BY_NAME:
                    raise KeyError(f"PATHS names an unknown check: {tok}")
                picked.append(tok)
        sel.checks.update(picked)
        sel.why[path] = (glob, picked)
    if paths:
        sel.checks.update(c.name for c in CHECKS if c.stage == "lint")
    if sel.all_cases:
        sel.cases = set(cases)
    return sel


def skill_of(path: str) -> str:
    parts = path.split("/")
    return parts[2] if parts[0] == ".agents" else parts[1]


def default_base() -> str:
    for ref in ("fork/main", "origin/main", "main"):
        r = subprocess.run(["git", "merge-base", "HEAD", ref], cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.strip()
    return "HEAD"


def changed_paths(base: str) -> list:
    """Paths that differ between `base` and the working tree, untracked included."""
    out = subprocess.run(["git", "diff", "--name-only", base], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.split()
    out += subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.split()
    return sorted(set(out))


# --- running ---------------------------------------------------------

def shellcheck_cmd():
    if shutil.which("shellcheck"):
        base = ["shellcheck"]
    else:
        r = subprocess.run(SHELLCHECK_PY + ["--version"], cwd=ROOT, capture_output=True)
        if r.returncode != 0:
            return None
        base = SHELLCHECK_PY
    files = sorted({str(p.relative_to(ROOT)) for g in SHELL_FILES for p in ROOT.glob(g) if p.is_file()})
    return base + files


def fmt(seconds: float) -> str:
    return f"{seconds:6.1f}s" if seconds >= 0.1 else "  <0.1s"


def run_check(c: Check, verbose: bool) -> str:
    """'ok', 'fail' or 'skip: <why>'."""
    cmd = c.cmd
    if c.name == "shellcheck":
        cmd = shellcheck_cmd()
        if cmd is None:
            return "skip: shellcheck is not installed and uvx cannot fetch it (CI runs it)"
    if c.needs and not shutil.which(c.needs):
        return f"skip: {c.needs} is not on PATH (CI runs it)"
    env = dict(os.environ, **c.env)
    if verbose:
        return "ok" if subprocess.run(cmd, cwd=ROOT, env=env).returncode == 0 else "fail"
    with tempfile.TemporaryFile("w+") as log:
        rc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        if rc != 0:
            log.seek(0)
            sys.stdout.write(log.read())
    return "ok" if rc == 0 else "fail"


def evals_command(cases) -> list:
    if cases is None:
        return ["tools/run-evals.sh"]
    return [f"tools/run-evals.sh --case {c}" for c in sorted(cases)]


def run_behavior(cases, run: bool) -> bool:
    """`cases` None means every case. Prints, or runs with --run-evals."""
    if cases is not None and not cases:
        print("  no eval case covers the changed paths")
        return True
    cmds = evals_command(cases)
    if not run:
        print("  evals cost model calls; run them with --run-evals, or:")
        for cmd in cmds:
            print(f"    {cmd}")
        return True
    ok = True
    for cmd in cmds:
        print(f"  $ {cmd}", flush=True)
        ok = subprocess.run(cmd.split(), cwd=ROOT).returncode == 0 and ok
    return ok


def list_stages() -> None:
    for stage, what in STAGES:
        checks = [c for c in CHECKS if c.stage == stage]
        total = sum(c.seconds for c in checks)
        head = f"{stage}  ({len(checks)} checks, ~{total:.0f}s)" if checks else f"{stage}  (evals: {', '.join(eval_cases())})"
        print(head)
        print(f"  {what}")
        for c in checks:
            print(f"  {fmt(c.seconds)}  {c.name}")
        print()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="tools/check.sh", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", action="append", choices=STAGE_NAMES, help="run this stage (repeatable)")
    ap.add_argument("--upto", choices=STAGE_NAMES, help="run every stage up to and including this one")
    ap.add_argument("--only", action="append", metavar="CHECK", help="run only this check (repeatable)")
    ap.add_argument("--changed", nargs="?", const="", metavar="BASE",
                    help="run only what the paths changed since BASE can break "
                         "(default: the merge base with main; HEAD: uncommitted work)")
    ap.add_argument("--explain", action="store_true", help="with --changed: print each path's row and checks")
    ap.add_argument("--run-evals", action="store_true", help="run the behavior stage's evals (costs money)")
    ap.add_argument("--list", action="store_true", help="list the stages and checks with measured times")
    ap.add_argument("-v", "--verbose", action="store_true", help="show every check's output")
    args = ap.parse_args(argv)

    if args.list:
        list_stages()
        return 0
    for name in args.only or []:
        if name not in BY_NAME:
            ap.error(f"unknown check {name!r}; --list shows them")

    if args.stage:
        stages = [s for s in STAGE_NAMES if s in args.stage]
    elif args.upto:
        stages = STAGE_NAMES[:STAGE_NAMES.index(args.upto) + 1]
    elif args.only:
        stages = sorted({BY_NAME[n].stage for n in args.only}, key=STAGE_NAMES.index)
    else:
        stages = ["lint", "shell", "unit"]
    if args.run_evals and "behavior" not in stages:
        stages.append("behavior")

    wanted = set(BY_NAME)
    cases = None                           # None: every case
    sel = None
    if args.changed is not None:
        base = args.changed or default_base()
        paths = changed_paths(base)
        sel = select(paths)
        wanted = set(sel.checks)
        cases = None if sel.cases == set(eval_cases()) else sel.cases
        print(f"changed since {base[:12]}: {len(paths)} paths")
        if args.explain:
            for p in paths:
                glob, picked = sel.why[p]
                print(f"  {p}  [{glob or 'no row: shell and unit whole'}] {' '.join(sorted(picked))}")
        for p in sel.unmapped:
            print(f"  no row in PATHS for {p}: shell and unit run whole")
        if not paths:
            print("nothing changed")
            return 0
    if args.only:
        wanted &= set(args.only)

    started = time.time()
    for stage in stages:
        checks = [c for c in CHECKS if c.stage == stage and c.name in wanted]
        if stage == "behavior":
            print("== behavior", flush=True)
            if not run_behavior(cases, args.run_evals):
                print("FAILED at stage behavior")
                return 1
            continue
        if not checks:
            continue
        print(f"== {stage} ({len(checks)})", flush=True)
        t0 = time.time()
        failed = []
        for c in checks:
            t = time.time()
            status = run_check(c, args.verbose)
            mark = {"ok": "ok  ", "fail": "FAIL"}.get(status, "skip")
            note = status[len("skip: "):] if status.startswith("skip") else ""
            print(f"  {mark} {fmt(time.time() - t)}  {c.name}{'  (' + note + ')' if note else ''}", flush=True)
            if status == "fail":
                failed.append(c.name)
        print(f"   {stage}: {fmt(time.time() - t0).strip()}", flush=True)
        if failed:
            print(f"FAILED at stage {stage}: {', '.join(failed)}")
            return 1

    if sel is not None:
        later = [s for s in STAGE_NAMES if s not in stages]
        rest = sorted(n for n in sel.checks if BY_NAME[n].stage in later)
        if rest:
            print(f"not run (outside the stages asked): {' '.join(rest)}")
            base_arg = f" {args.changed}" if args.changed else ""
            upto = max((BY_NAME[n].stage for n in rest), key=STAGE_NAMES.index)
            print(f"  tools/check.sh --changed{base_arg} --upto {upto}")
        if "behavior" in later and sel.cases and not args.only:
            print(f"eval cases for these changes: {' '.join(sorted(sel.cases))}")
            for cmd in evals_command(cases):
                print(f"  {cmd}")
    print(f"all passed in {time.time() - started:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
