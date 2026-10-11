# tools

Checks that keep the skills honest. All are plain Python 3 with no
dependencies; `check-cli.py` and `check-symbols.py` use the plugin's own
`bin/rbt` / `bin/uv`, so they test against exactly the Reboot version
the plugin pins.

| Tool | What it measures | Fails when |
| --- | --- | --- |
| `budget.py` | Words an agent reads before writing code, per front door (the SKILL.md files every build reads, the dashboard's included, plus each step's required references); `--readme write` refreshes the README table | `--check`: the README table is stale, or a front door's minimal path is over its ceiling (a cut lowers it; a raise is a record in `budget.py` of the findings the words are for and the signal that judges them; `--ceilings` prints it) |
| `check-cli.py` | Every `rbt …` command and `.rbtrc` line vs `rbt --help` | a flag or subcommand is unknown |
| `check-symbols.py` | Every `reboot…` import / dotted name / stdlib call vs the pinned package | a symbol doesn't resolve and isn't a tracked upstream defect in `known-defects.json` |
| `templates-drift.py` | The three templates' shared files are byte-identical; `DIFFERS` lists the ones that differ by design, with the reason; `--sync <template>` propagates one template's copies | a shared file differs, or a `DIFFERS` entry no longer does |
| `templates-smoke.sh` | Copies each `skills/build/templates/<front-door>/` (the ones named as arguments, default all three), then `rbt generate`, npm build, mypy, pytest (`SMOKE_FULL=1` runs the scenarios, as `--full` does) | any step fails |
| `gen-index.py` | Rewrites every `<!-- generated:start … -->` region in the SKILL.md files from reference frontmatter; enforces the map's invariants | `--check`: a region differs from its generated form, or an invariant breaks |
| `lint-references.py` | Frontmatter on every reference; the seven template sections on converted ones | a field or section is missing or out of order |
| `lint-frontmatter.py` | Front matter on every other Markdown file (below) | a file has no front matter block, or lacks its category's keys |
| `run-evals.sh` | Behavior: what a fresh agent decides with and without the plugin (`evals/`, via `claude plugin eval`); `--smoke` for one cheap run, a cached result served unless `--fresh`, each grader's votes per run after (`evals/README.md`; the cache key is in `evals_cache.py`) | not run in CI (it costs model calls); exits 1 if a case scores under `--threshold` |
| `style-check.py` | The four template stylesheets agree (web is the source; MCP adds `.ui`); `--browser` renders `style-check.html`, a page using every class, at 320/375/1280 px in light and dark (`--screenshots DIR` saves PNGs) | a copy drifts; the page overflows a screen or cuts off a short label |
| `findings.py` | Schema + summary of `findings/`; `--todo` lists the open items with the fixes the combined report names, grouped by file, with a mechanism to try | an item breaks the schema, or a `resolved_by` names a file, section, function or grader that doesn't exist (`findings/README.md`) |
| `check-manifests.py` | The JSON manifests parse; the Reboot version pins (`VERSION`, the manifests, `bin/rbt`, the templates' `pyproject.toml`) agree; each marketplace entry with a local source matches that plugin's own manifest (name, and version: a Claude marketplace entry must carry one); the Codex marketplace names only plugins the Claude one has | a manifest doesn't parse, two pins differ, or an entry and its plugin disagree |
| `check-mods.sh` | Each mod in `mods/` as the engine reads it: `claude plugin validate`, then its `*.test.ts` with `claude plugin test` | validation or a test fails |
| `check-facts.py` | Facts (inline code, error texts, Never leads, numbers, link targets) under `skills/` at a git revision (`--base`, default `HEAD`) that the working tree no longer has anywhere | not in `check.sh`: a review aid during a rewrite; exits 1 when a fact is gone |
| `check.sh` | Runs everything above in stages; `check.py` holds the stages, the checks and the path table (see Stages) | a check fails |
| `package-plugin.sh` | Zips the committed plugin (manifest, skills, hooks, shims, README) as a `.plugin` file the Claude app installs from a chat; `dependencies` dropped since the app runs no mods | (not a check) |

- `known-defects.json` — symbols missing because of an upstream bug,
  each tied to the finding that tracks it. Remove an entry when the
  fix ships. `reflib.py` is the shared frontmatter model the others import.

## Stages

`check.sh` runs the checks and the tests in `tests/` in stages, cheapest
first, and stops after the first stage that fails. Times measured on a
Mac with the downloads cached; `--list` prints every check's.

| Stage | Checks | Time | Protects |
| --- | --- | ---: | --- |
| `lint` | gen-index, lint-references, lint-frontmatter, findings, budget, style, templates-drift, manifests | <1 s | the text: generated regions, front matter, the budget, copies that must agree |
| `shell` | shellcheck over every shell script (`bin/uvx` fetches it when not installed) | 1 s | the hooks, shims and template scripts as shell |
| `unit` | the 27 unittest files under `tests/`, in a pool as wide as the machine; `serial` ones (real ports) after it | 20 s (55 s one at a time) | each hook, shim, template script and tool, against fakes and temp dirs |
| `integration` | check-cli, check-symbols, the schema guard on a fetched Node, the template tests under pytest, style-check `--browser`, templates-smoke (`SMOKE_FULL=1`, 2.5 to 4 min), the mods when `claude` is on PATH | 3 to 4.5 min; network | the skills against the pinned Reboot; the templates built and their scenarios run |
| `behavior` | the evals (`run-evals.sh`) | model calls, money | what an agent decides; prints the cases and the command unless `--run-evals`, which runs them with `--smoke` (`--full-evals` for the full run) |

```sh
tools/check.sh                      # lint, shell, unit (= check-all.sh)
tools/check.sh --upto integration   # (= check-all.sh --full)
tools/check.sh --stage unit         # one stage; --only <check> for one check
tools/check.sh --changed [BASE]     # only what the changed paths can break
tools/check.sh --changed --explain  # and which PATHS row picked each check
tools/check.sh --list               # and each check's last and median time here
tools/check.sh --stage unit -j 4    # a narrower pool (or CHECK_JOBS=4); -j 1 runs one at a time
tools/check.sh --stage integration --skip templates-smoke
tools/check.sh --only templates-smoke --template web-app
tools/check.sh --changed BASE --stage integration --dry-run   # `would run:` lines, nothing run
```

Inside a stage the order is fail-first: the checks the uncommitted
changes select, then those that failed in the last run, then the rest
by measured time, shortest first. Each run's times and results are
kept in `.reboot/check-history.json` (gitignored, this machine only);
`--list` shows each check's last and median time beside the table's,
and a check that takes more than twice its median (and a second over
it) prints a `warn` line. The unit stage prints each check's line as
it finishes and the output of a failed check after the stage's lines;
a check marked `serial` in `check.py` (it binds real ports) runs alone
after the pool.

### Pre-commit hook

`tools/githooks/pre-commit` runs `tools/check.sh --changed HEAD --upto
shell` (lint, and shellcheck when a shell file changed) over the
staged and unstaged changes, in about two seconds, and blocks the
commit on a failure (`git commit --no-verify` skips it). Install it
once per clone:

```sh
git config core.hooksPath tools/githooks
```

It is the repository's own hook, not the templates' `.githooks/`.

`--changed` diffs the working tree (untracked files included) against
BASE, by default the merge base with `fork/main` (else `origin/main`);
`--changed HEAD` takes uncommitted work only. `PATHS` in `check.py` maps
each path to the checks it can break (skills text: check-cli,
check-symbols and the eval cases whose graders load that skill;
templates: the template tests, shellcheck, the smoke; hooks: the hook
tests; `bin/`, `lib/`: the shim tests; a tool or a test: its own test;
`mods/`: the mods). `lint` runs whole on any change; a path no row
matches runs `shell` and `unit` whole. `--changed` honors `--stage`
and `--upto`: it runs the selected checks inside the stages asked,
and a stage it leaves empty prints `== <stage>: skipped, ...` and
passes. templates-smoke builds only the templates the changes lie in
(`skills/build/templates/<front-door>/...`); a shared file
(`copy.sh`, the templates' README, the shims, `VERSION`) builds all
three. `check-all.sh` is a wrapper kept for habits and docs.

`.github/workflows/skills-checks.yml` runs lint, shell and unit as
separate steps, the mods, the integration stage less the smoke in one
job, and the smoke as a matrix of three parallel jobs, one per
template. On a pull request the integration and smoke jobs run
`--changed <the PR's base>` and pass at once when the changes select
nothing of theirs (a `plan` step's `--dry-run` decides, so a skipped
job restores no cache); on a push to `main` they run whole. Both cache
uv's downloads (`UV_CACHE_DIR=~/.cache/uv`), npm's (`~/.npm`), uv's
Pythons and the shims' pinned binaries (`~/.claude/plugins/data/reboot/bin`),
keyed on `VERSION`, `lib/install_*.sh` and the templates'
`pyproject.toml`, `package.json` and any lockfiles.

## Front matter

Every `.md` starts with a YAML front matter block (flat `key: value`
lines and inline `[a, b]` lists), except two kinds of file: the
`README.md` files listed in `EXEMPT` (the root, `evals/`, `findings/`,
`mods/`, `tools/`, `skills/build/templates/` and the migrations'),
because GitHub shows front matter as a table on a directory's landing
page, and the templates' `FINDINGS.md`, `AGENTS.md`, `CLAUDE.md` and
`deploy/api-exceptions.md`, which `copy.sh` copies into the user's
project. Build output (`node_modules`, `dist`, `.venv`, the caches) is
skipped only inside a template or a mod. `lint-frontmatter.py` checks
each category's required keys; the full rules live with its owner:

| Files | Required keys | Full rules |
| --- | --- | --- |
| `skills/*/SKILL.md` | `name`, `description` | the plugin host |
| `skills/*/references/*.md` | `summary`, … | `lint-references.py`, `skills/_template.md` |
| `findings/*/*.md` | `id`, … | `findings.py`, `findings/README.md` |
| `evals/*/prompt.md`, `evals/*/graders/*.md` | grader `type` | `claude plugin eval` |
| everything else | `title`, `summary`, `kind`, `audience` | here |

Everything else uses this schema:

```yaml
---
title: "<the file's heading, plain>"
summary: "<one line, ≤ 18 words: what a reader gets from it>"
kind: migration          # migration | index | report | backlog
audience: agent          # agent | maintainer
applies: [mcp-ui, web-app, backend-only]  # migration only: front doors it touches
when: "<condition>"      # migration only, optional: omit when every app on them is affected
---
```

A migration note has no version field: its directory names the release.

## Adding or changing a reference

Edit the reference's frontmatter (`summary`, `step`, `applies`, `when`,
…; see `skills/_template.md`), then run `tools/gen-index.py`. Never edit
a generated list by hand.

Baseline numbers: `findings/BASELINE.md`.
