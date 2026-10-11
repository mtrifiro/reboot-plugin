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
    tools/check.sh --stage integration --skip templates-smoke
    tools/check.sh --only templates-smoke --template web-app
    tools/check.sh --changed BASE --stage integration --dry-run

A stage runs all its checks, prints each one's line as it finishes and
the stage's time, and the run stops after the first stage with a
failure. The output of a failed check is printed at the end of its
stage (`-v` prints every check's). The unit stage runs its checks in a
pool as wide as the machine (`-j N`, or CHECK_JOBS); a check marked
`serial` (real ports, global state) runs alone after the pool.

Inside a stage the order is fail-first: the checks the uncommitted
changes select, then those that failed last time, then the rest by
measured time, shortest first. Each run's times and results go to
`.reboot/check-history.json` (gitignored); `--list` shows each check's
last and median time, and a check that takes more than twice its
median prints a warning.

The behavior stage only prints the eval cases and the
`tools/run-evals.sh` command unless `--run-evals` is given; it runs
them with `--smoke` (one run, Haiku judging) unless `--full-evals`.

STAGES, CHECKS and PATHS below are the whole configuration.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import fnmatch
import json
import os
import re
import shutil
import statistics
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
    "install.sh", "hooks/*.sh", "hooks-handlers/*.sh", "lib/*.sh", "bin/*", "tools/*.sh", "tools/githooks/*",
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
    serial: bool = False        # binds real ports or reads global state: never beside another


def unit(path: str, seconds: float, serial: bool = False) -> Check:
    name = path[len("tests/"):-len("_test.py")]
    return Check(name, "unit", ["python3", path, "-q"], seconds, file=path, serial=serial)


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
    unit("tests/hooks/orphans_test.py", 4.5),
    unit("tests/hooks/schema_guard_test.py", 6.1),   # skips itself without a cached Node
    unit("tests/hooks/suite_guard_test.py", 1.1),
    unit("tests/hooks/session_start_test.py", 0.7),
    unit("tests/hooks/remind_test.py", 0.3),
    unit("tests/shims/rbt_test.py", 5.0),
    unit("tests/shims/uv_test.py", 4.8),
    unit("tests/templates/copy_test.py", 1.9),
    unit("tests/templates/run_progress_test.py", 0.04),   # skips itself without pytest
    unit("tests/templates/step_order_test.py", 0.04),     # skips itself without pytest-bdd
    unit("tests/templates/ports_test.py", 4.9, serial=True),        # binds a port copy.sh probes
    unit("tests/templates/test_sh_test.py", 0.04),        # skips itself without pytest
    unit("tests/templates/feature_lint_test.py", 0.04),   # skips itself without pytest-bdd
    unit("tests/templates/harness_hygiene_test.py", 0.04),
    unit("tests/templates/api_lint_test.py", 0.4),
    unit("tests/templates/doctor_test.py", 0.6),
    unit("tests/templates/placeholder_test.py", 5.3, serial=True),  # binds and serves ports
    unit("tests/templates/deploy_test.py", 0.1),
    unit("tests/tools/gen_index_test.py", 0.1),
    unit("tests/tools/findings_test.py", 0.2),
    unit("tests/tools/lint_frontmatter_test.py", 0.2),
    unit("tests/tools/check_manifests_test.py", 0.1),
    unit("tests/tools/check_cli_test.py", 0.04),
    unit("tests/tools/check_symbols_test.py", 0.04),
    unit("tests/tools/run_evals_test.py", 10.5),
    unit("tests/tools/check_transcript_test.py", 0.05),
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

# The front doors templates-smoke builds, in its default order. A change
# inside one template's directory smokes that template; any other path
# that selects the smoke (copy.sh, the shims, VERSION) smokes all three.
TEMPLATES = ["mcp-ui", "web-app", "both"]
TEMPLATES_DIR = "skills/build/templates/"

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
    ("tools/check-transcript.py", ["tools/check_transcript"]),
    ("tools/known-defects.json", ["check-symbols"]),
    ("tools/run-evals.sh", ["tools/run_evals", "shellcheck"]),
    ("tools/evals_cache.py", ["tools/run_evals"]),
    ("tools/style-check.*", ["style-browser"]),
    ("tools/templates-smoke.sh", ["shellcheck", "templates-smoke"]),
    ("tools/check-mods.sh", ["shellcheck", "mods"]),
    ("tools/check.py", ["tools/check"]),
    ("tools/githooks/*", ["shellcheck"]),
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
    templates: set = field(default_factory=set)   # what templates-smoke builds, when it is selected


def template_of(path: str):
    """The front door a path lies inside, or None (a shared file)."""
    if not path.startswith(TEMPLATES_DIR):
        return None
    parts = path[len(TEMPLATES_DIR):].split("/")
    return parts[0] if len(parts) > 1 and parts[0] in TEMPLATES else None


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
        if "templates-smoke" in picked:
            one = template_of(path)
            sel.templates.update([one] if one else TEMPLATES)
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


# --- history ---------------------------------------------------------

# Each check's recent times and its last result, per machine; written
# after every stage. A smoke of fewer than all three templates is kept
# under its own key ("templates-smoke[web-app]"), so it does not drag
# the whole smoke's median down.
HISTORY = ROOT / ".reboot" / "check-history.json"
KEEP = 20              # times kept per check
SLOW = 2.0             # warn past this many times the median ...
SLOW_FLOOR = 1.0       # ... and this many seconds over it (a 0.04 s check doubles on noise)


def load_history(path: Path | None = None) -> dict:
    try:
        data = json.loads((path or HISTORY).read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_history(hist: dict, path: Path | None = None) -> None:
    path = path or HISTORY
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.{os.getpid()}")
        tmp.write_text(json.dumps(hist, indent=1, sort_keys=True) + "\n")
        os.replace(tmp, path)
    except OSError:
        pass                # a record is a convenience; never fail a run over it


def median_time(hist: dict, key: str):
    times = (hist.get(key) or {}).get("times") or []
    return statistics.median(times) if times else None


def record(hist: dict, key: str, status: str, seconds: float) -> None:
    entry = hist.setdefault(key, {})
    entry["last"] = status
    if status in ("ok", "fail"):
        entry["times"] = (entry.get("times", []) + [round(seconds, 2)])[-KEEP:]


def slow_warning(hist: dict, key: str, seconds: float):
    """A line when `seconds` is past SLOW x the recorded median, else None."""
    times = (hist.get(key) or {}).get("times") or []
    if len(times) < 3:
        return None
    med = statistics.median(times)
    if seconds > SLOW * med and seconds - med > SLOW_FLOOR:
        return (f"  warn {key} took {seconds:.1f}s, {seconds / med:.1f}x its median of "
                f"{med:.1f}s over {len(times)} runs")
    return None


def fail_first(checks: list, first: set, hist: dict) -> list:
    """The changed paths' checks, then last run's failures, then the
    rest by measured time (the recorded median, else the table's)."""
    def key(c):
        med = median_time(hist, c.name)
        return (c.name not in first, (hist.get(c.name) or {}).get("last") != "fail",
                c.seconds if med is None else med)
    return sorted(checks, key=key)


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


def command_for(c: Check, templates) -> list:
    """`templates`: the front doors to smoke, or None for the default (all)."""
    if c.name == "shellcheck":
        return shellcheck_cmd()
    if c.name == "templates-smoke" and templates is not None:
        return c.cmd + [t for t in TEMPLATES if t in templates]
    return c.cmd


def history_key(c: Check, templates) -> str:
    if c.name == "templates-smoke" and templates is not None and set(templates) != set(TEMPLATES):
        return f"{c.name}[{','.join(t for t in TEMPLATES if t in templates)}]"
    return c.name


def run_check(c: Check, templates=None) -> tuple:
    """(status, output, seconds); status is 'ok', 'fail' or 'skip: <why>'."""
    t0 = time.time()
    cmd = command_for(c, templates)
    if cmd is None:
        return "skip: shellcheck is not installed and uvx cannot fetch it (CI runs it)", "", 0.0
    if c.needs and not shutil.which(c.needs):
        return f"skip: {c.needs} is not on PATH (CI runs it)", "", 0.0
    env = dict(os.environ, **c.env)
    with tempfile.TemporaryFile("w+") as log:
        rc = subprocess.run(cmd, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                            stdout=log, stderr=subprocess.STDOUT).returncode
        log.seek(0)
        out = log.read()
    return ("ok" if rc == 0 else "fail"), out, time.time() - t0


def run_stage(checks: list, jobs: int, verbose: bool, hist: dict, templates=None) -> list:
    """Runs `checks` (already in order), printing each line as it
    finishes; `jobs` > 1 runs those not marked serial in a pool, then
    the serial ones alone. Returns the failed checks' names; their
    output is printed after the stage's lines."""
    failed, outputs = [], []

    def report(c, status, out, seconds):
        mark = {"ok": "ok  ", "fail": "FAIL"}.get(status, "skip")
        note = status[len("skip: "):] if status.startswith("skip") else ""
        print(f"  {mark} {fmt(seconds)}  {c.name}{'  (' + note + ')' if note else ''}", flush=True)
        key = history_key(c, templates)
        warning = slow_warning(hist, key, seconds) if status in ("ok", "fail") else None
        if warning:
            print(warning, flush=True)
        record(hist, key, "skip" if note else status, seconds)
        if verbose and out:
            sys.stdout.write(out)
        if status == "fail":
            failed.append(c.name)
            outputs.append((c.name, out))

    pooled = [c for c in checks if not c.serial] if jobs > 1 else []
    alone = [c for c in checks if c not in pooled]
    if pooled:
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = {pool.submit(run_check, c, templates): c for c in pooled}
            for fut in concurrent.futures.as_completed(futures):
                report(futures[fut], *fut.result())
        if alone:
            print(f"  -- serial: {' '.join(c.name for c in alone)}", flush=True)
    for c in alone:
        report(c, *run_check(c, templates))
    if not verbose:
        for name, out in outputs:
            print(f"--- {name} output ---")
            sys.stdout.write(out if out.endswith("\n") or not out else out + "\n")
    return failed


def evals_command(cases, smoke: bool = False) -> list:
    flag = " --smoke" if smoke else ""
    if cases is None:
        return [f"tools/run-evals.sh{flag}"]
    return [f"tools/run-evals.sh{flag} --case {c}" for c in sorted(cases)]


def run_behavior(cases, run: bool, smoke: bool = True) -> bool:
    """`cases` None means every case. Prints, or runs with --run-evals;
    `smoke`: one run per case, Haiku judging (run-evals.sh --smoke)."""
    if cases is not None and not cases:
        print("  no eval case covers the changed paths")
        return True
    cmds = evals_command(cases, smoke)
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


def list_stages(hist: dict) -> None:
    print(f"  {'table':>7} {'last':>7} {'median':>7}  check   (last, median: this machine's runs, "
          f"{HISTORY.relative_to(ROOT)})")
    for stage, what in STAGES:
        checks = [c for c in CHECKS if c.stage == stage]
        total = sum(c.seconds for c in checks)
        head = f"{stage}  ({len(checks)} checks, ~{total:.0f}s)" if checks else f"{stage}  (evals: {', '.join(eval_cases())})"
        print(head)
        print(f"  {what}")
        for c in checks:
            times = (hist.get(c.name) or {}).get("times") or []
            last = fmt(times[-1]) if times else "      -"
            med = fmt(statistics.median(times)) if times else "      -"
            flags = "  (serial)" if c.serial else ""
            failed = "  (failed last run)" if (hist.get(c.name) or {}).get("last") == "fail" else ""
            print(f"  {fmt(c.seconds)} {last} {med}  {c.name}{flags}{failed}")
        for key in sorted(k for k in hist if k.startswith("templates-smoke[") and stage == "integration"):
            times = hist[key].get("times") or []
            if times:
                print(f"         {fmt(times[-1])} {fmt(statistics.median(times))}  {key}")
        print()


def default_jobs() -> int:
    try:
        return max(1, int(os.environ.get("CHECK_JOBS", "")))
    except ValueError:
        return os.cpu_count() or 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="tools/check.sh", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", action="append", choices=STAGE_NAMES, help="run this stage (repeatable)")
    ap.add_argument("--upto", choices=STAGE_NAMES, help="run every stage up to and including this one")
    ap.add_argument("--only", action="append", metavar="CHECK", help="run only this check (repeatable)")
    ap.add_argument("--skip", action="append", metavar="CHECK", help="leave this check out (repeatable)")
    ap.add_argument("--template", action="append", choices=TEMPLATES,
                    help="templates-smoke builds only this front door (repeatable; "
                         "with --changed, only if the changes select it)")
    ap.add_argument("--changed", nargs="?", const="", metavar="BASE",
                    help="run only what the paths changed since BASE can break "
                         "(default: the merge base with main; HEAD: uncommitted work)")
    ap.add_argument("--explain", action="store_true", help="with --changed: print each path's row and checks")
    ap.add_argument("--dry-run", action="store_true",
                    help="print `would run: <check>` for each check the flags select, run nothing")
    ap.add_argument("-j", "--jobs", type=int, default=default_jobs(),
                    help="unit checks run at once (default: CHECK_JOBS, else the CPU count)")
    ap.add_argument("--run-evals", action="store_true", help="run the behavior stage's evals (costs money)")
    ap.add_argument("--full-evals", action="store_true",
                    help="with --run-evals: run-evals.sh's full run (3 runs, the configured judge), not --smoke")
    ap.add_argument("--list", action="store_true", help="list the stages and checks with measured times")
    ap.add_argument("-v", "--verbose", action="store_true", help="show every check's output")
    args = ap.parse_args(argv)

    hist = load_history()
    if args.list:
        list_stages(hist)
        return 0
    for name in (args.only or []) + (args.skip or []):
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
    templates = set(args.template) if args.template else None   # None: all three
    first = set()                          # what the changes select: run first
    if args.changed is not None:
        base = args.changed or default_base()
        paths = changed_paths(base)
        sel = select(paths)
        wanted = set(sel.checks)
        first = set(sel.checks)
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
        if "templates-smoke" in wanted:
            templates = sel.templates & templates if templates is not None else set(sel.templates)
            if not templates:
                wanted.discard("templates-smoke")
                print(f"  templates-smoke: the changes touch only {' '.join(sorted(sel.templates))}, "
                      f"not {' '.join(args.template)}")
            elif args.explain:
                print(f"  templates-smoke builds: {' '.join(t for t in TEMPLATES if t in templates)}")
    else:
        try:
            first = select(changed_paths("HEAD"), {}).checks
        except (subprocess.CalledProcessError, OSError):
            first = set()
    if templates is not None and set(templates) == set(TEMPLATES):
        templates = None
    if args.only:
        wanted &= set(args.only)
    wanted -= set(args.skip or [])

    if args.dry_run:
        for stage in stages:
            if stage == "behavior":
                continue
            for c in fail_first([c for c in CHECKS if c.stage == stage and c.name in wanted], first, hist):
                extra = " " + " ".join(command_for(c, templates)[len(c.cmd):]) if c.name == "templates-smoke" else ""
                print(f"would run: {c.name}{extra}")
        return 0

    started = time.time()
    for stage in stages:
        if stage == "behavior":
            print("== behavior", flush=True)
            if not run_behavior(cases, args.run_evals, smoke=not args.full_evals):
                print("FAILED at stage behavior")
                return 1
            continue
        all_in_stage = [c for c in CHECKS if c.stage == stage]
        checks = fail_first([c for c in all_in_stage if c.name in wanted], first, hist)
        if not checks:
            if args.stage or sel is not None:
                why = "the changed paths select none of its checks" if sel is not None else "the flags leave none"
                print(f"== {stage}: skipped, {why} "
                      f"({' '.join(c.name for c in all_in_stage)})", flush=True)
            continue
        jobs = args.jobs if stage == "unit" else 1
        print(f"== {stage} ({len(checks)}{f', {jobs} at once' if jobs > 1 else ''})", flush=True)
        t0 = time.time()
        failed = run_stage(checks, jobs, args.verbose, hist, templates)
        save_history(hist)
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
            for cmd in evals_command(cases, smoke=True):
                print(f"  {cmd}")
    print(f"all passed in {time.time() - started:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
