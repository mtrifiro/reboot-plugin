# __Title__ — map for a coding agent

A Reboot app (Python backend, React + Vite web app). Read this first;
the Reboot plugin's skills have the rest. Keep this file current: when
a file moves, a command changes or a rule is learned the hard way,
change it here in the same commit.

## Where things live

| What | Where |
|---|---|
| API (the schema): state types, methods, errors | `api/__app__/v1/__app__.py` |
| Servicers (the behavior) | `backend/src/servicers/__app__.py` |
| **The one servicer list** | `backend/src/servicers/registry.py`: `main.py` and every test module take `SERVICERS` and `libraries()` from it. A new state type is added there, once |
| The application, OAuth, boot | `backend/src/main.py` |
| Generated code (not tracked, never edited) | `backend/api/`, `web/src/api/`; rebuilt by `uv run rbt generate` |
| Web app | `web/src/` (`App.tsx`, `styles.css` holds the design tokens) |
| Scenarios (the spec) | `tests/*.feature` |
| Test modules | `tests/*_test.py`; each `scenarios(...)` names the features it runs |
| Deploy, backup, restore | `scripts/deploy.sh`, `deploy/config`, `deploy/before-backend`, `scripts/backup.sh`, `scripts/restore.py` |
| The design and why each choice was made (read before changing it) | `design/design.md`, `design/decisions.md` (one entry per acceptance, appended) |
| The accepted design, what a change did to it (Design or Prove), the last test run, each deploy's release record | `design/accepted.json` and `design/review.md`, `scripts/model_diff.py`, `tests/.last-run.json`, `deploy/ledger.jsonl` |
| `rbt` config | `.rbtrc` (line-based, not YAML) |
| Ports (backend, dashboard, Vite), chosen at scaffold so projects on one machine don't meet | `.rbtrc` (`dev run --port`, `--dashboard-port`, `dashboard --port`), `web/vite.config.ts`, `web/.env.development`; `scripts/doctor.sh` says who answers on them |
| Surprises about Reboot or its skills | `FINDINGS.md` |

## Run, test, deploy

- **Generate:** `python3 scripts/api_lint.py && uv run rbt generate` after
  every change under `api/`; the lint refuses, with the fix, what
  `rbt generate` or the deploy would refuse later.
- **Run:** with the plugin's `run` skill, never bare `rbt dev run` or
  `npm run dev`.
- **Test:** `scripts/test.sh changed` while iterating (`smoke`,
  `backend`, `<area>`), `scripts/test.sh full` before a handoff or a
  push to `main`; then `uv run mypy backend/ tests/`. A full run takes
  minutes: run it in the foreground and wait for it. A scenario that
  hangs fails on its own after 300 s. When something fails for no
  reason you can see, `scripts/doctor.sh` first.
- **Deploy:** `scripts/deploy.sh`, with the plugin's `deploy` skill.
- **Workflow:** not chosen yet. At the first change after the first
  build the agent asks whether changes go straight onto `main` or onto
  a branch each, and writes the answer here. A push to `main` is
  refused unless the last full run passed on that exact tree
  (`.githooks/pre-push`; a clone runs `git config core.hooksPath
  .githooks` once).

## Rules that cost the most when broken

1. **Behavior first, then acceptance.** A feature starts as a `@wip`
   `.feature` file, agreed before the API or code changes; the user
   accepts the domain model and feature files before any
   implementation, and again after any change `model_diff.py` calls a
   design change (the plugin's `build/references/flywheel.md`).
2. **The API only grows.** Add fields, methods, errors and types; never
   remove or rename one, and never reword a method's `description=`
   (it is schema). A removal Reboot allows ships only when
   `deploy/api-exceptions.md` names it.
3. **Back up production on its own** before a deploy: `scripts/backup.sh
   prod` as a command by itself, not chained with `;` or piped through
   `tail` or `grep`, which hide a failure. `deploy.sh` does this for you.
4. **Nothing regenerates or rewrites code while the suite runs:** no
   `rbt generate`, `rbt dev run`, dev server or file edit. Tests then
   fail with `Method not found!` on unrelated methods.
5. **Servicers are listed only in `registry.py`.** One missing from a
   test's list fails only when called.
6. **Log surprises the moment they happen** in `FINDINGS.md`.
