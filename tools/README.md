# tools

Checks that keep the skills honest. All are plain Python 3 with no
dependencies; `check-cli.py` and `check-symbols.py` use the plugin's own
`bin/rbt` / `bin/uv`, so they test against exactly the Reboot version
the plugin pins.

| Tool | What it measures | Fails when |
| --- | --- | --- |
| `budget.py` | Words an agent reads before writing code, per front door; `--readme write` refreshes the README table | `--readme check`: the README table is stale (reports the budget; never enforces it) |
| `check-cli.py` | Every `rbt …` command and `.rbtrc` line vs `rbt --help` | a flag or subcommand is unknown |
| `check-symbols.py` | Every `reboot…` import / dotted name / stdlib call vs the pinned package | a symbol doesn't resolve and isn't a tracked upstream defect in `known-defects.json` |
| `templates-smoke.sh` | Copies each `skills/build/templates/<front-door>/`, then `rbt generate`, npm build, mypy, pytest | any step fails |
| `gen-index.py` | Rewrites every `<!-- generated:start … -->` region in the SKILL.md files from reference frontmatter; enforces the map's invariants | `--check`: a region differs from its generated form, or an invariant breaks |
| `lint-references.py` | Frontmatter on every reference; the seven template sections on converted ones | a field or section is missing or out of order |
| `lint-frontmatter.py` | Front matter on every other Markdown file (below) | a file has no front matter block, or lacks its category's keys |
| `run-evals.sh` | Behavior: what a fresh agent decides with and without the plugin (`evals/`, via `claude plugin eval`) | not run in CI (it costs model calls); exits 1 if a case scores under `--threshold` |
| `style-check.py` | The four template stylesheets agree (web is the source; MCP adds `.ui`); `--browser` renders `style-check.html`, a page using every class, at 320/375/1280 px in light and dark (`--screenshots DIR` saves PNGs) | a copy drifts; the page overflows a screen or cuts off a short label |
| `findings.py` | Schema + summary of `findings/` | an item breaks the schema, or a `resolved_by` section doesn't exist |

`check-all.sh` runs them in order (`--full` adds the CLI, symbol and
template-build checks); `.github/workflows/skills-checks.yml` runs both
in CI.

- `known-defects.json` — symbols missing because of an upstream bug,
  each tied to the finding that tracks it. Remove an entry when the
  fix ships. `reflib.py` is the shared frontmatter model the others import.

## Front matter

Every `.md` starts with a YAML front matter block (flat `key: value`
lines and inline `[a, b]` lists), except two kinds of file:
`README.md` files, because GitHub shows front matter as a table on a
directory's landing page, and `build/templates/*/FINDINGS.md`, which
`copy.sh` copies into the user's project. `lint-frontmatter.py` checks
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
kind: migration          # migration | index | report
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
