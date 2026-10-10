---
id: plugin-browser-07
project: plugin-browser
source: "plugin-browser/FINDINGS.md § Plugin skills, item 5"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - build/SKILL.md
  - feature/SKILL.md
  - python/references/testing-features.md
  - build/references/evidence.md
  - build/references/flywheel.md
tags: [testing, operations, pattern]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "build/templates/README.md § Files"
---
# Tests: no way to run only what a change touches, and no check that `main` got a full run

**What happened.** The app grew to 101 scenarios (64 backend at ~17 s each, 37 in a browser at ~20 s), so a full `uv run pytest` takes 30+ minutes. While iterating, the agent either ran everything or hand-built `-k` filters, and twice a full run hung at teardown for 30 minutes. The project works on `main` (no pull requests), so `prove.yml` never ran, and nothing showed that what was pushed had passed a full run; the template's `tests/.last-run.json` can't show it either, since a full run usually happens before the commit (`dirty: true`) and `revision` + `dirty` can't prove the commit equals the tested code. What fixed both here: an area tag on every feature file (`@scan`, `@element`, `@claude`, …, registered as markers in `pytest.ini`), `@smoke` on 8 scenarios, a `browser` marker added in `conftest.py` to everything in `web_test.py`; a `scripts/test.sh` with `changed` (the areas the uncommitted files touch, from a file → area table, plus `@smoke`; a change to `api/`, fixtures or `conftest.py` asks for `full`), `<area>…`, `smoke`, `backend` and `full`; `full` records the hash of the exact tree it passed on (a temporary index, `git add -A`, `git write-tree`), refusing to record it if files changed during the run; and a `pre-push` hook (`.githooks/`, `core.hooksPath`) that refuses a push to `master` whose tree differs from that record outside Markdown files (`--no-verify` skips it on purpose). In `pytest.ini`, `--recording-slowmo=0 --recording-dwell=0` (about 4 s less per browser scenario) and `pytest-timeout` (300 s, `signal`), so a hang fails one scenario instead of stalling the run. A typical change now runs in about 3–8 minutes, and a push to `master` still always follows a complete green run.

**Expected.** The templates and skills to give this shape for free: tagged areas and a `scripts/test.sh` in every template; build Step 6 and the feature skill saying "while iterating, run the touched areas; before handoff or a push, `full`"; and the "always a complete run" half for `Workflow: main` projects too. The cheapest version builds on what exists: add the tested tree's hash to `tests/.last-run.json` (`last_run.py`), and ship a pre-push hook that checks it (`full: true`, `failed: 0`, matching tree) for a push to `main`; on branches `prove.yml` keeps gating the merge.

**Repro.** Any app past ~50 scenarios with `Workflow: main`: iterate on one page, then push.

**Where in the skills.** `build/SKILL.md` § Step 6 — Tests; `feature/SKILL.md` (running scenarios while iterating); `python/references/testing-features.md` § Tags and § Limits (custom tags appear only as a dashboard limitation); `build/references/evidence.md` (`.last-run.json`); `build/templates/*/tests/last_run.py`, `pytest.ini`, `tests/conftest.py`; `build/references/flywheel.md` § Where the work happens (`Workflow: main` gets no `prove.yml`).

**Resolution (2026-10-10).** `scripts/test.sh` in every template: `changed` (the feature files changed since a revision, through the modules that run them), `smoke`, `backend`, `<area>` (one `@<area>` tag per feature file, registered in `pytest.ini`) and `full`; `tests/last_run.py` records the hash of the tree a run passed on and `.githooks/pre-push` refuses a push to `main` of any other tree, so a `main` workflow has the gate `prove.yml` gives branches; `pytest-timeout` fails a hung scenario on its own.
