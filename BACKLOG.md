---
title: "Backlog"
summary: "Agreed plugin work not started yet, each with its design notes and open questions."
kind: backlog
audience: maintainer
---

# Backlog

Work agreed on but not started. Each item says what it is, why, how it
would work, and what's still open. Move an item out when its work lands.

The model for both items is the Releases view in `alt-dashboard`
(`web/src/changelog/ReleasesPage.tsx`, `backend/src/history_reader.py`):
per-revision rows of ADDED / CHANGED / REMOVED grouped API · DATA, CODE
and SPEC, with "N scenarios call it · passing" on changed methods.

## 1. Change report at handoff

**What.** When a build or an update hands back, show what it changed,
grouped like the Releases view:

```
API · DATA  3
  ADDED    type    Site
  ADDED    method  Site.overview
  CHANGED  data    SiteSnapshot.daily   list[int] → list[DailyCount]
CODE  4
  CHANGED  method  Site.refresh   body changed
SPEC  2
  ADDED    scenario  A brand-new site with no visits says so
```

**Why.** The model's narration says what it meant to do; this says what
the code now is, from the files. It needs no recorder, so it works for
every app.

**How.**
- A stdlib-only Python script shipped with the plugin (say
  `skills/build/scripts/change_report.py`), run with `python3`.
- `--snapshot` records a parsed summary of the project into
  `.rbt/change-report/baseline.json`:
  - API files (`api/**/*.py`, AST): models with each field's tag, name
    and type; state types; methods with kind and `description=`. The
    schema guard (`mods/reboot-schema-guard/hooks/schema.ts`) parses
    the same shape.
  - Code (`backend/src/**/*.py`, generated code excluded): a digest of
    each function's and method's AST, keyed `Type.method` (servicer
    class names without `Servicer`) or `module:function`, as
    `history_reader.py`'s `code_symbols` does.
  - Spec (`tests/**/*.feature`): scenario titles per file.
- `--report` compares the project with the baseline and prints the
  grouped rows as Markdown, capping each group with "and N more".
- The build skill snapshots before Step 1 (a new app: an empty baseline)
  and at Update Flow step 1, and shows the report in the Step 7
  handoff.

**Open.**
- A snapshot file, or `git` when the project is a repository? The
  snapshot works without git (build projects aren't always
  repositories); `--since <ref>` could be added for those that are.
- A new app's first report lists everything as ADDED. Summarize it
  instead (counts per group), and give rows only for updates?
- The handoff already carries the app URL and test result; keep the
  report short enough not to bury them.

## 2. Scenario-to-method recorder in the build templates

**What.** Every app records, per scenario run, which methods it called
and whether it passed, so the change report (1) can say "20 scenarios
call it · passing / not verified" beside each changed method and put a
pass dot on each scenario.

**Why.** A changed method nobody's scenarios call is a blind spot; the
annotation shows it at the moment the change is reported.

**How.**
- Ship the recorder alt-dashboard reads (its only copy:
  `reboot-crm/tests/testboard_recorder.py`) in each build template's
  `tests/`, registered from `conftest.py`. It wraps Reboot's
  `Middleware.create_context` and counts `StateType.method` per running
  test, writing `.test-results/<run>/<pid>.jsonl` with a `calls` map
  per result line.
- Keep its format alt-dashboard's, so alt-dashboard works on any app the
  plugin builds (`TESTBOARD_PROJECT=/path/to/app`).
- `.test-results/` in each template's `.gitignore`.
- The change report reads the latest results: "verified" when the
  latest result passed and neither the code fingerprint nor the
  scenario's feature file changed since, as alt-dashboard decides it
  (`backend/src/project_files.py`).

**Open.**
- Its tree fingerprint must match alt-dashboard's `project_files.py`
  (checked there by `tests/project_files_test.py`): which repository
  owns the format?
- It wraps a framework internal (`Middleware.create_context`): check it
  on each Reboot upgrade, and add it to the upgrade skill's checks.
- Cost: a few lines per test run; confirm it doesn't slow the suite.
