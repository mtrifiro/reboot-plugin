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

Plain Claude also builds a web app without asking on the `route-*`
prompts, so those cases guard against regressions more than they show
a gain over no plugin. `mcp-ready` and the design case are where the
plugin's effect shows (no plugin: 0–1 of 3 and 0 of 3).

LLM graders use the default Haiku judge unless you pass
`--judge-model sonnet`, which is more reliable on these rubrics; each
grader asks the judge to quote the sentence it relied on. A check for
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
`plugin.json`) and copies results into `evals/results/` (gitignored).
Each run is a full Claude session on your credentials; the default model
is your session's. Add `--max-cost-usd <n>` to cap a run.

## Add a case

`claude plugin eval init --bare <name>` inside a wrapper, or copy a case
here: `prompt.md` (front matter: `runs`, `max_turns`, `timeout_seconds`,
`allowed_tools`, `append_system_prompt`; quote any value with a colon)
and one file per grader in `graders/`. Reference:
https://code.claude.com/docs/en/plugin-evals.md
