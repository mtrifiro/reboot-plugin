# tools

Checks that keep the skills honest. All are plain Python 3 with no
dependencies; `check-cli.py` and `check-symbols.py` use the plugin's own
`bin/rbt` / `bin/uv`, so they test against exactly the Reboot version
the plugin pins.

| Tool | What it measures | Fails when |
| --- | --- | --- |
| `budget.py` | Words an agent reads before writing code, per front door; `--readme write` refreshes the README table | `--ceilings`: a front door is over its ceiling in `budget-ceilings.json`; `--readme check`: the README table is stale |
| `check-cli.py` | Every `rbt …` command and `.rbtrc` line vs `rbt --help` | a flag or subcommand is unknown |
| `check-symbols.py` | Every `reboot…` import / dotted name / stdlib call vs the pinned package | a symbol doesn't resolve and isn't a tracked upstream defect in `known-defects.json` |
| `templates-smoke.sh` | Copies each `skills/build/templates/<front-door>/`, then `rbt generate`, npm build, mypy, pytest | any step fails |
| `gen-index.py` | Rewrites every `<!-- generated:start … -->` region in the SKILL.md files from reference frontmatter; enforces the map's invariants | `--check`: a region differs from its generated form, or an invariant breaks |
| `lint-references.py` | Frontmatter on every reference; the seven template sections on converted ones | a field or section is missing or out of order |
| `findings.py` | Schema + summary of `findings/` | an item breaks the schema, or a `resolved_by` section doesn't exist |

`check-all.sh` runs them in order (`--full` adds the CLI, symbol and
template-build checks); `.github/workflows/skills-checks.yml` runs both
in CI.

- `budget-ceilings.json` — per-front-door word ceilings. A ratchet:
  lower one when a change brings the path under it (the tool says
  when); never raise one to make a change fit.
- `known-defects.json` — symbols missing because of an upstream bug,
  each tied to the finding that tracks it. Remove an entry when the
  fix ships. `reflib.py` is the shared frontmatter model the others import.

## Adding or changing a reference

Edit the reference's frontmatter (`summary`, `step`, `applies`, `when`,
…; see `skills/_template.md`), then run `tools/gen-index.py`. Never edit
a generated list by hand.

Baseline numbers: `findings/BASELINE.md`.
