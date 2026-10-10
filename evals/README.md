# Behavior evals

Cases for `claude plugin eval`: each gives a fresh Claude a prompt, with
and without this plugin, and grades what it decides. They check what the
skills tell an agent to do, which `tools/check-all.sh` can't.

Runs are read-only (`Read`, `Glob`, `Grep`, `Skill`, `AskUserQuestion`)
and told they can't write, so each one ends after the decisions the
skills front-load (which front door, the design) and before any code.

| Case | Checks |
| --- | --- |
| `route-default-todo`, `route-default-crm` | No front door named: web app first, no question, backend ready for MCP |
| `route-mcp` | Claude named as the runtime: MCP UI first, backend ready for a web app |
| `route-just-website` | "just a website": one front door, no MCP offer |
| `route-both` | Both named: both front doors on one backend |
| `design-ready-for-both` | The design has a `User` type, each method's AI role, AI-facing descriptions, a visual brief with a primary view, light/dark modes with a toggle, and dev-only demo data |
| `design-look-triage` | Triage of a few hundred bug reports: a grouped list (not a chart) as the primary view, color on one dimension, stat tiles and labelled filters |
| `design-look-board` | A dozen candidates through interview stages: still a board, so the principles add flexibility rather than a new house style |
| `design-roles` | A hotel with front desk and housekeeping: the design names the roles and enforces in the backend which methods each may call; dev-only demo data |
| `design-accept-gate` | The accept checkpoint: the design maps each rule to its owner, method, kind and caller, and stops for the user's acceptance. `explains-the-stop` (the stage card's plain words for why it stops) is reported, not scored: a planning session never reaches the checkpoint with the artifacts in hand, and no run has produced the card yet |
| `design-skip-gate` | Told up front to build without stopping: the design is still shown, and nothing waits |

Plain Claude also builds a web app without asking on the `route-*`
prompts, so those cases (and every `no-question` grader) guard against
regressions more than they show a gain over no plugin: `route-both`,
`route-just-website` and `route-mcp` score the same in both arms.
`mcp-ready` and the design cases are where the plugin's effect shows
(no plugin: 0–3 of 3 on `mcp-ready` across runs, so it is noisy; 0 of 3
on the design cases). The gate cases, three runs per arm on 2026-10-10:
`design-accept-gate` 0.53 with the plugin, 0.00 without (two of the
three plugin runs stopped for acceptance; one went on), and
`design-skip-gate` 1.00 with, 0.56 without.

`tools/run-evals.sh` copies the skills into its wrapper rather than
linking them (a run may read inside the plugin under test, judged by the
real path; through a link every reference read was denied and the
design cases measured the SKILL.md text alone), leaves the
leftover-process hook out of the wrapper (it reports this machine's dev
processes, which is not the skills), and passes `--judge-model sonnet`
unless you pass a judge yourself: Haiku failed designs that plainly met a rubric. Each
LLM grader asks the judge to quote the sentence it relied on. A check for
something that sits late in a long design (`light-dark`, `demo-data`) is
a `regex` grader: a judge failed designs that plainly had those
sections, likely because it doesn't see the whole of a long message.

`tool_used: Skill` graders show which skills loaded; the runner doesn't
score them in the with/without comparison, so every behavior that counts
has its own scored grader.

## Run

```sh
tools/run-evals.sh                        # every case, 3 runs per arm
tools/run-evals.sh --tag routing --runs 1 # a quick pass
tools/run-evals.sh --case design-ready-for-both
```

The script wraps the working tree as a plugin (the repo has no
`plugin.json`; the mods are not under eval, and every run is a read-only
planning session, so the feature skill's red-then-green loop, the schema
guard and the run, deploy and report skills have no eval yet) and copies
results into `evals/results/` (gitignored).
Each run is a full Claude session on your credentials; the default model
is your session's. Add `--max-cost-usd <n>` to cap a run.

## Add a case

`claude plugin eval init --bare <name>` inside a wrapper, or copy a case
here: `prompt.md` (front matter: `runs`, `max_turns`, `timeout_seconds`,
`allowed_tools`, `append_system_prompt`; quote any value with a colon)
and one file per grader in `graders/`. Reference:
https://code.claude.com/docs/en/plugin-evals.md
