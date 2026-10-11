# Behavior evals

Cases for `claude plugin eval`: each gives a fresh Claude a prompt, with
and without this plugin, and grades what it decides. They check what the
skills tell an agent to do, which `tools/check-all.sh` can't.

Runs are read-only (`Read`, `Glob`, `Grep`, `Skill`, `AskUserQuestion`)
and told they can't write, so each one ends after the decisions the
skills front-load (which front door, the design) and before any code.

| Case | Checks |
| --- | --- |
| `route-default-todo`, `route-default-crm` | No front door named: web app first, no question about which, backend ready for MCP |
| `route-mcp` | Claude named as the runtime: MCP UI first, backend ready for a web app |
| `route-just-website` | "just a website": one front door, no MCP offer |
| `route-both` | Both named: both front doors on one backend |
| `design-ready-for-both` | Asks one round of scope questions with options (or states the answers when no one can answer) and says it builds something simple first; the design has a `User` type, each method's AI role, AI-facing descriptions, a visual brief with a primary view, light/dark modes with a toggle, dev-only demo data, and no growing history list on an app-lifetime actor |
| `design-look-triage` | Assumes first; triage of a few hundred bug reports: a grouped list (not a chart) as the primary view, color on one dimension, stat tiles and labelled filters |
| `design-look-board` | Assumes first; a dozen candidates through interview stages: still a board, so the principles add flexibility rather than a new house style |
| `design-roles` | Assumes first; a hotel with front desk and housekeeping: the design names the roles and enforces in the backend which methods each may call; roles on one roster, a sign-in linked only on a verified email, the first admin named; dev-only demo data |
| `design-accept-gate` | The review on the first prototype: the agent asks one round of scope questions (or states the answers) and says it builds something simple first, designs the whole initial prototype saying each object and decision with its why, maps each rule to its owner, method, kind and caller, lists what goes beyond the brief, puts the user's acceptance at the running prototype's handoff, explains the Reboot ideas behind the model in the app's own terms, and says nothing in the first person. `explains-the-stop` (the review's plain words: what it covers and the answers it takes) runs on the plugin arm only, so it is reported under the with-without ablation and scored when the baseline arm is off |
| `design-accept-gate-unnamed` | The accept gate's case with a prompt that never names Reboot, so the reminder hook stays silent: what the skills do alone. The other design cases name Reboot, as a user starting a build does (since 2026-10-11; scores before that date ran without the reminder on `design-accept-gate` and `design-skip-gate`) |
| `design-skip-gate` | Told up front to build without stopping: the design is still shown, nothing waits, the build teaches Reboot as it goes, and nothing is said in the first person |
| `workflow-ask-once` | A todo app after its first build, with no workflow line in AGENTS.md: the first change asks whether changes go onto `main` or a branch each, before any edit, and pushes or opens nothing unasked |
| `workflow-recorded` | The same app with `Workflow: main` recorded in AGENTS.md: the change goes onto `main` and nothing asks about branches again |

Plain Claude also builds a web app without asking on the `route-*`
prompts, so those cases guard against regressions more than they show a
gain over no plugin (their front-door graders allow questions about the
domain and fail only a question about which kind of app; `no-question`
survives only on `design-skip-gate`, the bypass): `route-both`,
`route-just-website` and `route-mcp` score the same in both arms.
`mcp-ready` and the design cases are where the plugin's effect shows
(no plugin: 0 to 3 of 3 on `mcp-ready` across runs, so it is noisy; near
zero on the design cases). The design cases, three runs per arm on
2026-10-11: `design-accept-gate` 0.90 with the plugin, 0.00 without,
under the prototype-first flow (assumptions, one feature built and
reviewed running); the rest under the flow an hour earlier, which asked
first: `design-skip-gate` 1.00 and 0.33; `design-look-triage` 0.87 and
0.33; `design-look-board` 0.78 and 0.44; `design-ready-for-both` 0.71
and 0.00; `design-roles` 0.60 and 0.33. On the accept gate the plugin's
gain is the assumptions said up front, the rule mapping and the review
placed on the running app, in every run (measured before the whole
prototype replaced one feature first). `narrates-objects` has since
passed 3 of 3 with the plugin on three runs of the case. Plain
Claude also asks before it builds in a planning session, so
`waits-for-acceptance` guards against a regression more than it shows
a gain. An earlier wording of that
grader asked for a stop after the API and feature files, a moment a
planning session never reaches, and failed runs that had stopped at the
features; it scored 0.53 with the plugin before the rewording.

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

The script wraps the working tree as a plugin (the copies of the
skills and the hooks need a plugin of their own; the mods are not under
eval, and every run is a read-only planning session, so the feature skill's red-then-green loop, the schema
guard and the run, deploy and report skills have no eval yet) and copies
results into `evals/results/` (gitignored).
The `workflow-*` cases start from a fixture (`scaffold_script`), which
the runner skips without `--scaffold`, so the script adds `--scaffold`
whenever a selected case has one, unless you pass `--scaffold` or
`--no-scaffold` yourself.
Each run is a full Claude session on your credentials; the default model
is your session's. Add `--max-cost-usd <n>` to cap a run.

## Add a case

`claude plugin eval init --bare <name>` inside a wrapper, or copy a case
here: `prompt.md` (front matter: `runs`, `max_turns`, `timeout_seconds`,
`allowed_tools`, `append_system_prompt`; quote any value with a colon)
and one file per grader in `graders/`. Reference:
https://code.claude.com/docs/en/plugin-evals.md
