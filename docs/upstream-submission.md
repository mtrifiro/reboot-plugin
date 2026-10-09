---
title: "Submitting ia-restructure upstream as #186-style stacked PRs"
summary: "How the branch becomes five stacked PRs to reboot-dev/reboot, without findings or mods."
kind: report
audience: maintainer
---

# Submitting `ia-restructure` upstream as #186-style stacked PRs

## Context

The skills work on `ia-restructure` (69 commits on top of `origin/main` 1f4f7bf, 913 files, +43.6k/−13.5k) has to go upstream. Upstream is **not** `reboot-dev/reboot-plugin`, which is a release mirror ("[Release] Synchronize for release"). The real home is the monorepo **`reboot-dev/reboot`, under `reboot/plugin/`**, which is where #186 lands.

#186 sets the format:
- Many small commits, each standalone. The headline is `Area: plain-English change` (`Skills:`, `Dashboard:`, `Plugin:`), and the body says what was wrong, then what changed. Every commit ends with a `Co-Authored-By` trailer.
- The PR body is just "See commits." It goes from a branch to `main`, and benh reviews it.

Decisions made:
- **findings/ stays out.** It stays in the fork and reboot-findings.
- **mods/ stays out.** That covers reboot-progress, reboot-schema-guard, the marketplace wiring for them, and the `run_progress.py` test-run recorder that only the band reads.
- **Stacked PRs.** Each PR in the stack holds small commits in #186 style.

What the branch looks like without findings/ and mods/: about 378 files, +28.7k/−13.5k, in roughly 35 commits that matter.

## Upstream drift to absorb

- **Monorepo changes since our base.**
  - `9316156` and `604c90c` (Sep 30, `reactively()`) changed `skills/python/references/testing-external-context.md`. We restructured that file, so it will conflict.
  - The same commits added `skills/upgrade/migrations/next/reactively-yields-response-or-aborted.md`. That file is new, so it won't conflict.
- **#186 (onelxj, open, waiting on benh).** It edits 15 skill files that our Phase 1 and concision passes rewrote: `lifecycle-*`, `patterns-common-gotchas`, `state-collections`, `testing-*`, `web-app/SKILL.md`, `run`, `dashboard`. Ask for #186 to **land first**. Then port its facts into the restructured files while rebasing PR 1, and use `tools/check-facts.py` to confirm none of them was dropped.
- **#193 (riley, draft).** It changes how the dashboard starts in the skills, so it overlaps our `dashboard` and `build` spine. Tell riley about the stack so whichever PR lands second gets rebased.

## Mechanics

1. **Leave `ia-restructure` alone.** It stays the working branch, and the other session keeps committing beside it. Do all the submission work in a fresh clone: `git clone ~/projects/reboot-plugin ~/projects/reboot-plugin-submit`.
2. **Strip excluded paths from every commit** with `git filter-repo --invert-paths`:
   - `findings/`, `mods/`, `BACKLOG.md`, `tools/__pycache__/`, `.DS_Store`
   - Commits that only touched findings disappear on their own: 7a86de1, d193a90, c8885e7, ce31632, 83c375c, 450c372.
   - The ~30 Band/mod commits shrink to whatever they changed outside `mods/`.
3. **Make content edits on top of the filtered history** for the things a path filter can't remove:
   - Remove the mod entries from `.claude-plugin/marketplace.json`.
   - Remove `tests/run_progress.py` and its `conftest.py` imports from the three templates, along with the `.reboot/` gitignore lines.
   - Remove the test-run-record section of `testing-project-setup.md`, which came in with a4c4a1d and ed2fe14.
   - Make `tools/check-cli.py`, `lint-frontmatter.py`, `check-all.sh` and the CI workflow skip findings when `findings/` is missing. Drop `tools/findings.py`.
4. **Curate with a scripted rebase** (`GIT_SEQUENCE_EDITOR`, because interactive rebase isn't available).
   - **Reorder** the commits so that each PR's commits sit next to each other (see below).
   - **Fold away churn**:
     - 4b06874 "Remove the reading-budget ceilings" goes into 18a2073 and 2895945, so the ceilings are never added.
     - The leftover skill changes from the mod commits become fixups or get dropped.
   - **Split commits that mix concerns, by path**:
     - b248c4d and 3ac4c56 are partly evals and partly skills.
     - b248c4d also covers template look steps, MCP host theme and shared stylesheets. Split those three into separate commits.
     - 9d3fca2 keeps only `tools/`, since its findings part is gone.
   - **Reword** every message to #186's form: `Skills:` / `Build:` / `Deploy:` / `Hooks:` / `Plugin:` headline, then a body that says what was wrong and what changes. Drop "Phase N" and "BASELINE" wording, which reviewers won't have context for.
   - **Check every commit** with `git rebase --exec 'tools/check-all.sh'`.
5. **Port into the monorepo.**
   - Clone `reboot-dev/reboot` and confirm that `reboot/plugin/` on `main` equals our base plus the drift listed above.
   - Run `git format-patch` for each PR's range, then apply it with `git am -3 --directory=reboot/plugin` on a branch for that PR. Resolve the `testing-external-context.md` conflict and the #186 overlaps along the way.
   - **Paths outside the plugin.** A `.github/workflows/skills-checks.yml` inside `reboot/plugin/` won't run, so turn it into a Bazel test target or a workflow at the monorepo root, following how `reboot/plugin/BUILD.bazel` already does it. Add the new templates and tools to the plugin's BUILD filegroups.
6. **Push and open the PRs**:
   - Push branches named `mtrifiro.skills_*` in onelxj's `name.topic` style, to `reboot-dev/reboot` if you can push there, or to a fork if not.
   - Open each PR against the one below it. The body is "See commits.", one line saying what it is based on, and the attribution line. Request review from benh.

## The stack

**PR 1 — `Skills: one reference template, generated indexes, and the checks that hold them`.** This is the restructure, and it should change no behavior.
- **Tooling:**
  - budget, drift and lint checks (9d3fca2 tools part)
  - reference template and lint (75d2d91)
  - generated reference indexes (952af9e)
  - generated error index (948d68b)
  - CI, the FINDINGS.md convention and the `report` skill (18a2073)
  - check-facts (e979744)
  - front matter on every Markdown file, and its lint (2985537)
- **Content:**
  - reference conversions and splits (dc13298, 5c97439)
  - shared build spine, real templates and dissolved gotcha lists (4bba4fd)
  - concision pilot and passes 1–2 (03b59f5, 2895945, f494b89, b7c306e)
  - US spelling (01aaa4e)
- **Evidence for reviewers:** a `check-facts.py` report against `main` showing that no fact was dropped. Put it in the PR body, below "See commits."

**PR 2 — `Skills: design and build flow`.** Each commit is one behavior change:
- web apps default to a highly visual UI (e0dd17b)
- every backend is ready for both front doors, and the web app is built first (6618032)
- hand off only after the tests finish, and keep tabs and forms inside the page (8724ae3)
- name the AI roles and the theme toggle in the design (3ac4c56, skills part)
- template look steps, MCP host theme and shared stylesheets (b248c4d, split by concern)
- Reboot's brand is the default look (c905da6)
- tell the user state types and methods as the build writes them (3bb0852)
- Google's responsiveness thresholds (441632e)
- the feature skill handles fixes too (c1f9fde)
- servicers/registry.py (d148c05)
- AGENTS.md and a one-line CLAUDE.md (fa389fb)

**PR 3 — `Skills: runtime fixes`.** These are small and independent, so they could go up first if PR 1 stalls:
- vendor reboot.std.oauth for 1.6.0 (357f22c)
- the dashboard reuses only a dashboard this session started (7f37e23)
- report orphaned dashboards at session start (dedef85)

**PR 4 — `Deploy: scripts/deploy.sh and backups`:**
- templated deploy.sh (0f219c4)
- every deploy backs up first, with a restore procedure (d0d0e35, about 3.5k lines)

**PR 5 — `Skills: behavior evals`.** These are additive:
- routing evals (50135a3)
- design-phase evals (b248c4d, eval part)
- the grader fixes in 3ac4c56
- `tools/run-evals.sh`

Not submitted: findings/, mods/ (including the band's `run_progress.py`), BACKLOG.md (4aa5306).

## Critical files

- `.claude-plugin/marketplace.json`: drop the mod dependencies
- `skills/build/templates/{both,web-app,mcp-ui}/tests/{conftest.py,run_progress.py}` and `.gitignore`
- `skills/python/references/testing-project-setup.md` and `testing-external-context.md`
- `tools/check-all.sh`, `check-cli.py`, `lint-frontmatter.py`, `findings.py`
- `.github/workflows/skills-checks.yml`
- the monorepo's `reboot/plugin/BUILD.bazel`

## Verification

- **At every curated commit:** `tools/check-all.sh` passes (`rebase --exec`).
- **At the tip of each PR:**
  - `tools/templates-smoke.sh` passes.
  - `tools/check-facts.py` against `main` reports no dropped facts, including #186's.
- **Same content after the port:** `git diff` between the filtered reboot-plugin tip and the monorepo branch's `reboot/plugin/` is empty, apart from the drift and #186 changes we absorbed.
- **In the monorepo:** the plugin's Bazel targets build and test, and CI on each PR is green.
- **Optional:** `tools/run-evals.sh` on the PR 2 tip, to show that routing and design behavior hold.
