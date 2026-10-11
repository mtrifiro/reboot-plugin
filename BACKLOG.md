---
title: "Backlog"
summary: "Agreed plugin work not started yet, each with its design notes and open questions."
kind: backlog
audience: maintainer
---

# Backlog

Work agreed on but not started. Each item says what it is, why, how it
would work, and what's still open. Move an item out when its work lands.

The model for items 1 and 2 is the Releases view in `alt-dashboard`
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
    schema guard (`hooks/schema-guard/schema.ts`) parses
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

## 3. References no build is told to read

**What.** About 15 references carry `step: any`, `step: run` or
`step: deploy`, and the build skill renders reading lists only for the
shell, api, servicer, auth, frontend and tests steps. So no list names
them, and agents rarely open them: `patterns-load-and-benchmarking.md`,
`patterns-react-state.md`, `lifecycle-dockerfile.md`,
`lifecycle-dev-loop.md` among them.

**Why.** Found through the Plugin Browser's "What app builds skip"
panel (deferred 2026-10-10). The panel blamed agents for skipping files
the plugin never told them to read.

**How.** Give each a real step, a `when:` that a skill renders, or both;
or render an "any time" list in the build skill. `tools/gen-index.py`
generates the lists, and `tools/budget.py` must stay under its
ceilings.

**Open.**
- Which references deserve a step and which only a `when:`.
- The Plugin Browser side (`~/projects/plugin-browser`): count
  step-any, run and deploy items as on demand, not required, and judge
  a build only against items that existed when it started.

## 4. The `one-color-dimension` grader fails even with the plugin

**What.** `evals/design-look-triage/graders/one-color-dimension.md`
wants the design to name one accent color and keep status color for a
single data dimension (such as severity), with other statuses neutral.
In the 2026-10-09 runs it failed with the plugin as well as without.

**Why.** A grader that fails with the plugin measures nothing about
it: either `web-app/references/ui-design.md` doesn't say this clearly
enough for the design step, or the grader asks for more than the skill
teaches.

**How.** Read the runs' design text against the grader. Then fix
whichever is wrong: the principle in `ui-design.md` (and the build
skill's five-line visual brief), or the grader's wording.

**Open.** Whether the rule belongs in the design phase at all, or in
the frontend step's look checks.

## 5. Codex's PATH is frozen at install time

**What.** `install.sh` writes `shell_environment_policy.set.PATH` into
`~/.codex/config.toml` as the plugin's `bin/` followed by the
installer's own PATH. Codex's setting replaces PATH wholesale, so
anything the user adds to their PATH later never reaches Codex's
shells until the installer runs again.

**Why.** A tool installed after the plugin (a new Node, `gh`, a
Homebrew package in a new place) is invisible to Codex with no error,
only "command not found".

**How.** Prepend instead of replace, if Codex's config can express it
(an `include` or an inherit-and-prepend form). Otherwise a session-start
check that warns when the baked PATH lacks entries the current PATH
has, and says to re-run the installer.

**Open.** Whether Codex supports prepending in config at all; check
its current `shell_environment_policy` documentation.

## 6. Shellcheck over the templates' scripts

**What.** `tools/check-all.sh` runs shellcheck over the plugin's own
scripts but not the templates' (`scripts/deploy.sh`, `backup.sh`,
`deploy/before-backend`, in each of the three templates).

**Why.** Every Reboot app ships these scripts, and `deploy.sh` is
hundreds of lines that touch production. It was left out on
2026-10-10 because another session had `deploy.sh` in flight.

**How.** Add the templates' shell scripts to the shellcheck line and
fix what it finds once. `tools/templates-drift.py` keeps the three
copies identical, so a fix goes through `--sync`.

**Open.** Nothing beyond the findings themselves.

