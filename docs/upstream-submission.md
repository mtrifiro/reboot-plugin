---
title: "Submitting ia-restructure upstream"
summary: "The whole plan: talk to the maintainer first, inventory and isolate what could read as hacky, send corrections before opinions as stacked #186-style PRs, each risky group droppable, then keep a cadence."
kind: report
audience: maintainer
---

# Submitting `ia-restructure` upstream

## Where it stands

On 2026-10-11 `ia-restructure` was 246 commits on top of upstream's
`1f4f7bf` (2026-09-16): 1,111 files, about +69.6k/−14.1k lines. About
37% of the changed files are under `findings/`, which never goes up.
Most of the rest is skills, references, templates and evals. Refresh
these numbers when the work starts: `git rev-list --count
$(git merge-base HEAD origin/main)..HEAD` and `git diff --shortstat`.

**Upstream** is the monorepo **`reboot-dev/reboot`, under
`reboot/plugin/`**, where #186 lands. `reboot-dev/reboot-plugin` is a
release mirror ("[Release] Synchronize for release"), never a target.

**#186 sets the format:**
- Many small commits, each standalone. The headline is `Area:
  plain-English change` (`Skills:`, `Build:`, `Deploy:`, `Hooks:`,
  `Plugin:`). The body says what was wrong, then what changed. Every
  commit ends with a `Co-Authored-By` trailer.
- The PR body is "See commits." It goes from a branch to `main`, and
  benh reviews it.

**The risk is not the size.** A 70k-line branch can be split. The risk
is arriving with an unrequested redesign of the product all at once,
with a history that wanders, and with text that reads as routing
around Reboot's own defects. So the plan below:
1. talks to the maintainer before any PR (Phase 0);
2. inventories and isolates everything that could read as hacky
   (Phase 1);
3. gathers evidence a reviewer can check (Phase 2);
4. sends corrections before opinions, as stacked PRs in which every
   risky group is its own PR that nothing below depends on, so it can
   be declined without blocking the rest (The stack);
5. keeps a cadence afterwards, so the fork never drifts this far again.

## Phase 0: talk to the maintainer first

Before any code goes up, send benh (or whoever owns `reboot/plugin/`)
a short write-up and a demo, and agree the direction.

1. **The write-up**, one page:
   - What a first-time builder hits on upstream `main`, from the
     findings: the counts (576 findings from 36 projects on
     2026-10-11; 97 of them Reboot, `reboot.bdd` or Cloud defects),
     and three concrete examples.
   - What the branch changes, in the four tiers of The stack below,
     and that tier C is a proposal.
   - The Plugin Browser's Changes page (`~/projects/plugin-browser`,
     `#/changes`) is the long form: its "In short", "The parts that
     changed" and its 17 themes. Export or screenshot what helps.
2. **The demo:** one prompt, such as "a hotel app for staff and
   guests", built on upstream `main` and on the branch, side by side.
   Show the transcripts' shape (`tools/check-transcript.py <project>`),
   the reports, the running apps, and the test results.
3. **The questions to settle:**
   - Do they want tier C (the build's conversation, the Flywheel, the
     reports, `design.md`) at all, as a series, or as an option?
   - The steering hooks (tier C, last PR): in the plugin, or not?
   - Where the checks run in the monorepo (Bazel targets or a root
     workflow).
   - Whether they want the 97 Reboot defects filed as issues before
     the PRs (Phase 1 assumes yes).
4. **Record the answers** at the top of this file, dated, and adjust
   the stack before Phase 1's moves.

## Phase 1: inventory what could read as hacky

Upstream should never meet text that routes around a Reboot defect
without an issue behind it, a private project's name, or a mechanism
that polices the model without its reason. Build this inventory in the
working tree of `ia-restructure`, before the submission clone.

**Sources.** Five, because a finding's `target` alone misses some:

1. **Findings about Reboot.** Every finding whose frontmatter `target`
   is `framework`, `bdd` or `cloud` (97 on 2026-10-11: 67, 26 and 4),
   any `status`. Follow `resolved_by` to the skill section it names,
   and add the sections `~/projects/reboot-findings/workarounds.json`
   lists in `refs` under that finding's id.
2. **Workarounds hidden under plugin findings.** When a skill was
   silent about a Reboot quirk, the finding was often tagged `plugin`,
   because the fix was skill text. Scan `skills/` itself, whatever the
   tag, for workaround patterns: version caveats ("on 1.6.0", "until a
   release", "Reboot intends to"), process kills and signals (`pkill`,
   SIGINT rules), heap or environment settings (`NODE_OPTIONS`), and
   "never X while Y" rules. Also read the titles of the 371
   plugin-targeted findings for ones that describe Reboot's behavior.
3. **Private project citations in `skills/`.** Parenthesized tags
   naming a project, such as `(reboot-crm, 1.6.0)`: 75 in 37 files on
   2026-10-11. Find them with `grep -rnoE '\((<the project names from
   ls findings/>)[^)]*\)' skills`.
4. **Hooks and scripts.** Two kinds, listed apart:
   - **Guards** that compensate for a Reboot defect:
     `hooks-handlers/orphans.sh`, `hooks/suite-guard.sh`,
     `hooks/schema-guard.sh`, the templates' `.githooks/pre-push`, and
     any added since.
   - **Steering hooks** that hold the model to the skills' own rules,
     because written instructions alone did not:
     `hooks-handlers/welcome.sh` (refuses tool calls until the welcome
     is visible, re-prompts at Stop), `reports.sh` (sends a report
     saved but not shown), `quiet.sh` (repeats the step-line rule
     every 12 calls), `remind.sh` (re-injects guidance each prompt),
     and `bin/reboot-now` with its auto-approve case. Each needs its
     evidence: the session it fixed and what the session did without it.
5. **Workarounds outside `skills/`.** Template scripts and test
   fixtures (`skills/build/templates/*/scripts/`, `tests/`), and the
   tools that cite findings: `tools/budget.py`'s ceiling records cite
   finding ids such as `P3.94`, `tools/check-facts.py` and
   `tools/findings.py` read `findings/`.

**For each line, record:** the source, the finding id (if any) and its
title, the Reboot version, the file and section, the passage, and
whether the defect still reproduces on the Reboot version the plugin
pins now (`still_applies`, or check it again).

**Give each line one disposition:**
- **Keep as guidance:** it describes how Reboot is meant to work, so
  it isn't a workaround. Drop its project citation.
- **Move to known issues:** move it out of the main guidance into the
  skill's `references/known-issues.md`, following
  `skills/dashboard/references/known-issues.md`. Each entry: symptom,
  Reboot version, workaround, "remove when fixed", upstream issue link.
- **File upstream:** the defect has no Reboot issue yet. File it with
  the `report` skill, after the user approves the batch, before the PRs
  go out, so the known-issues entry can cite it.
- **Drop:** it no longer reproduces, so the passage goes.
- **Guard:** the hook stays. Its header and README line name the issue
  it mitigates.
- **Own PR, droppable:** it is a deliberate choice upstream may not
  want (the steering hooks, anything in tier C). It goes in a PR of its
  own at the top of its tier, and nothing below it depends on it.

**Write the inventory** to `docs/upstream-workaround-inventory.md`:
one table per disposition (source, finding, file and section, version,
issue), with the counts at the top. The user approves it before
anything moves.

**Apply it.**
- Moves, drops and guard comments go into `ia-restructure` as ordinary
  commits, so the working branch matches what upstream will see.
- Citations are replaced in the submission clone only (Mechanics, step
  3), so the working branch keeps its provenance. Each becomes the issue
  link, or `(Reboot 1.6.0)` when there is none.
- Tools that read `findings/` learn to skip it when it is missing
  (Mechanics, step 3). Ceiling records in `budget.py` keep their reason
  in words and lose the finding ids.

## Phase 2: the evidence package

Each PR's body stays "See commits." plus one line saying what it is
based on. The evidence goes in the Phase 0 write-up and, where a PR
needs it, in a comment on it:
- **Corrections (tier A):** `tools/check-facts.py` against `main`
  showing no fact dropped, including #186's; and per fact corrected,
  the finding behind it, without project names.
- **Known issues:** the filed issue numbers, one per entry.
- **Infrastructure (tier B):** CI green on each PR; `tools/templates-smoke.sh`
  on the templates; the eval pass rates from `tools/run-evals.sh`.
- **Tier C:** the side-by-side demo, `tools/check-transcript.py` on a
  real build (welcome first, every report framed, no lines between
  reports but step lines), and the findings it closed.

## Upstream drift to absorb

Recheck all of these when the work starts; the list is from 2026-10-10.
- **Monorepo changes since our base.**
  - `9316156` and `604c90c` (Sep 30, `reactively()`) changed
    `skills/python/references/testing-external-context.md`. We
    restructured that file, so it will conflict.
  - The same commits added
    `skills/upgrade/migrations/next/reactively-yields-response-or-aborted.md`.
    That file is new, so it won't conflict.
- **#186 (onelxj, open, waiting on benh).** It edits 15 skill files our
  restructure rewrote: `lifecycle-*`, `patterns-common-gotchas`,
  `state-collections`, `testing-*`, `web-app/SKILL.md`, `run`,
  `dashboard`. Ask for #186 to **land first**, then port its facts into
  the restructured files while rebasing, and confirm with
  `tools/check-facts.py` that none was dropped.
- **#193 (riley, draft).** It changes how the dashboard starts in the
  skills, overlapping our `dashboard` and `build` spine (the dashboard
  now opens once the code is written). Tell riley about the stack, so
  whichever lands second is rebased.

## Mechanics

0. **Phases 0 and 1 first.** The direction is agreed and the
   inventory's moves and drops are applied on `ia-restructure`.
1. **Leave `ia-restructure` alone.** It stays the working branch, and
   other sessions keep committing beside it. Do all submission work in a
   fresh clone: `git clone ~/projects/reboot-plugin
   ~/projects/reboot-plugin-submit`.
2. **Strip excluded paths from every commit** with `git filter-repo
   --invert-paths`: `findings/`, `mods/`, `BACKLOG.md`,
   `tools/__pycache__/`, `.DS_Store`. Commits that only touched those
   disappear; the band commits shrink to what they changed outside
   `mods/`.
3. **Make content edits on top of the filtered history**, for what a
   path filter can't remove:
   - the mod entries in `.claude-plugin/marketplace.json`;
   - `tests/run_progress.py`, its `conftest.py` imports and the
     `.reboot/` gitignore lines in the three templates, and the
     test-run-record section of `testing-project-setup.md`;
   - the tools that read `findings/` (`check-cli.py`,
     `lint-frontmatter.py`, `check.sh`, `check-all.sh`,
     `check-facts.py`, the CI workflow) skip it when it is missing;
     drop `tools/findings.py`;
   - every private project citation in `skills/`, as the inventory
     says;
   - finding ids in `tools/budget.py`'s ceiling records, replaced by
     their reasons in words.
4. **Curate with a scripted rebase** (`GIT_SEQUENCE_EDITOR`;
   interactive rebase isn't available here).
   - **Group** commits into the PRs of The stack. The Plugin Browser's
     `frontend/web/src/pages/changesThemes.tsx` assigns every commit
     on the branch to one or more of 17 themes (its `commits:` lists);
     the stack below is built from those themes.
   - **Split commits that span themes, by path.** A commit listed
     under several themes is split so each part lands in its PR.
   - **Fold churn into its final form.** One design reached in many
     steps becomes one commit stating the result. Examples: the
     welcome (about eight commits on 2026-10-11), the report frame and
     titles, the step lines (narration, then `reboot-now`, then
     branded lines), the budget ceilings (added, removed, added again).
     Upstream sees what was concluded, not how.
   - **Reword** every message in #186's form, without "Phase N",
     "BASELINE", project names or session ids.
   - **Check every commit** with `git rebase --exec
     'tools/check.sh --upto unit'`.
5. **Port into the monorepo.**
   - Clone `reboot-dev/reboot` and confirm `reboot/plugin/` on `main`
     equals our base plus the drift above.
   - `git format-patch` each PR's range and apply it with `git am -3
     --directory=reboot/plugin` on a branch per PR, resolving the drift
     and #186 overlaps.
   - **Paths outside the plugin.** A workflow inside `reboot/plugin/`
     won't run, so CI becomes Bazel test targets or a root workflow,
     as agreed in Phase 0, following `reboot/plugin/BUILD.bazel`. New
     templates, hooks and tools get filegroups.
6. **Push and open the PRs** as branches named `mtrifiro.skills_*`
   (onelxj's `name.topic` style), to `reboot-dev/reboot` if you can push
   there, else a fork. Each PR is opened against the one below it. The
   body is "See commits.", one line saying what it is based on, and
   the attribution line. Request review from benh.

## The stack

**Four tiers, least contested first.** Tier A is corrections, tier B
safety and infrastructure, tier C the opinionated product flow, tier D
stays in the fork. **The stack rule:** nothing in a lower tier depends
on a higher one, and every PR marked *droppable* can be declined
without blocking anything below it. Where a commit serves both a lower
and a higher PR, split it so the lower part stands alone.

Themes named in each PR are the Changes page's
(`changesThemes.tsx`); take their `commits:` lists at submission time,
minus the excluded paths, and curate as in Mechanics, step 4.

### Tier A: corrections, sent first

**A1. `Skills: runtime and fact corrections`.** Small, independent,
uncontested: what the skills said about Reboot that was wrong or
missing, each fact with the defect or behavior behind it. Includes
vendoring `reboot.std.oauth` for 1.6.0 (357f22c) and the dashboard
reusing only a dashboard this session started (7f37e23). Draw the rest
from the inventory's "keep as guidance" lines and the references
theme's content fixes. It can go up the moment Phase 0 agrees, even if
the rest stalls.

**A2. `Skills: one reference template, generated indexes, and the
checks that hold them`.** The restructure, with no behavior change:
the theme "References: one layout, generated reading lists" and the
reading budget from "Checks for the plugin's maintainers". The guide
groups' names in the user's terms (83b1ea2) belong here. Evidence: a
`check-facts.py` report against `main` showing no fact dropped.

**A3. `Skills: known issues in Reboot 1.6.0`, droppable.** The
inventory's "move to known issues" lines: one `references/known-issues.md`
per skill that has any, each entry citing its filed issue. Reviewers
see every workaround with its issue, apart from the guidance. If
upstream prefers to fix the defects instead, this PR shrinks as they
land.

### Tier B: safety and infrastructure

**B1. `Templates: every app starts from a working project`,** with
"Testing in every project": the three templates, `servicers/registry.py`,
the API lint, `scripts/test.sh` and the suite marker, the pre-push
rule, `AGENTS.md`, the house palette (1e9fed8). Without `run_progress.py`
(tier D).

**B2. `Deploy: scripts/deploy.sh, backups and restore`:** the theme
"Deploying, backing up and restoring".

**B3. `Hooks: guards`:** from "Hooks: rules that hold every time", the
guards only: the schema guard, the suite guard, auto-approve for the
plugin's own skills and files, the orphan report at session start, and
the PATH shims ("Shims and the installer"). Each hook's header names
the issue it mitigates. The hook tests move to `tests/reboot/plugin/hooks/`
with a `py_test` target, and `lib/own.sh` gets a filegroup.

**B4. `Checks and evals`:** "Checks for the plugin's maintainers" (the
five-stage `tools/check.sh`, CI that skips what a change can't break)
and "Evals: does the plugin change what an agent decides?". Additive.
`tools/check-transcript.py` comes with tier C, since it measures C's
rules.

**B5. `Codex`, droppable:** the theme "Codex", if upstream wants the
plugin to support it.

### Tier C: the opinionated flow, a proposal

Sent only as Phase 0 agreed, as one stacked series, each PR droppable
from the top down.

**C1. `Skills: one build process`:** the themes "Skills: one build
process" and "How the apps look": the shared design-and-build spine,
both front doors ready, rules first then the model then scenarios, the
visual and interactive default, the app never left broken.

**C2. `Skills: the Reboot Flywheel`:** "The Reboot Flywheel: the user
decides": the stage map and routing rule, acceptance recorded in the
repository (`design/accepted.json`, `review.md`, `model_diff.py`), the
release record, a first build designing through its running prototype,
the gate evals. Based on B2 (deploy) and B4 (evals).

**C3. `Skills: the build's conversation`:** "The build welcomes you,
asks about scope, and teaches Reboot" and "The build speaks in framed
reports, with one step line between": the welcome, the scope round and
brief, the six framed reports saved under `design/reports/`,
`design/design.md` as the one document to read, the voice rules, and
`tools/check-transcript.py`.

**C4. `Hooks: holding the build to its conversation`, droppable:** the
steering hooks from Phase 1, source 4 (`welcome.sh`, `reports.sh`,
`quiet.sh`, the per-prompt `remind.sh`) and `bin/reboot-now` with its
auto-approve case. Its commit messages carry the evidence: the session
each fixed and what it did without it. If upstream declines it, C3
still stands as written guidance.

### Tier D: stays in the fork

- `findings/` (it lives on in the fork and in `reboot-findings`), and
  `workarounds.json`.
- `mods/`, the progress band, with its marketplace wiring and the
  templates' `run_progress.py`.
- `BACKLOG.md`, and plans under `docs/` that only make sense here,
  including this file and the inventory.
- The Plugin Browser (its own repository).

## After the first PR: a cadence

- **Small and often.** Once A1 is in, send what is ready every week or
  two rather than holding it for a series. A new correction goes
  straight up as its own PR, never waiting on tier C.
- **Rebase weekly** on the monorepo's `reboot/plugin/` so drift stays
  small, and recheck the drift list.
- **One way in for new work.** Anything new on `ia-restructure` is
  tagged at commit time with its tier, so the next submission sorts
  itself.

## Critical files

- `.claude-plugin/marketplace.json`: the mod dependencies.
- `skills/build/templates/{both,web-app,mcp-ui}/tests/{conftest.py,run_progress.py}`
  and `.gitignore`.
- `skills/python/references/testing-project-setup.md` and
  `testing-external-context.md`.
- `tools/check.sh`, `check-all.sh`, `check-cli.py`,
  `lint-frontmatter.py`, `check-facts.py`, `findings.py`, `budget.py`.
- `.github/workflows/skills-checks.yml`.
- `hooks/hooks.json` and `hooks-handlers/`: split between B3 (guards)
  and C4 (steering).
- The monorepo's `reboot/plugin/BUILD.bazel`.

## Verification

- **At every curated commit:** `tools/check.sh --upto unit` passes
  (`rebase --exec`).
- **At the tip of each PR:**
  - `tools/templates-smoke.sh` passes;
  - `tools/check-facts.py` against `main` reports no dropped facts,
    including #186's;
  - no private project name appears: `grep -rnE '<the project names>'
    skills` is empty.
- **Droppable means droppable:** for each PR marked droppable, the PR
  below it with that PR removed still passes its checks.
- **Same content after the port:** `git diff` between the filtered
  submission tip and the monorepo branch's `reboot/plugin/` is empty,
  apart from the drift and #186 changes absorbed.
- **In the monorepo:** the plugin's Bazel targets build and test, and
  CI on each PR is green.
- **Behavior holds:** `tools/run-evals.sh` on the C1 and C3 tips, and
  `tools/check-transcript.py` on a real build from the C3 tip.
