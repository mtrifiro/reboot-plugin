---
name: upgrade
description: Upgrade an existing Reboot application to the latest Reboot version. Use when `rbt` prints "A newer Reboot (X.Y.Z) is available", when an application refuses to start because its `reboot` version does not match the `rbt` CLI, or when the user asks to upgrade/update Reboot. First talks the developer through updating the plugin itself when it is out of date, then applies the migration steps each intermediate release needs, bumps every version pin to the exact version the plugin ships, regenerates code, and runs the tests.
argument-hint: [<project-directory>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit, AskUserQuestion
---

# upgrade — Upgrade a Reboot Application

The single authoritative upgrade procedure. Triggers:

- `rbt` prints `A newer Reboot (X.Y.Z) is available; ...` — a
  `newer Reboot is available` notice is not blocking: ask the developer at a convenient moment; if they decline,
  keep iterating.
- An app refuses to start with `This application depends on reboot <X>, but it is being run by an rbt CLI at version <Y>`
  — blocking: switch to this skill unconditionally.
- The user asks to upgrade or update Reboot.

Never start an upgrade without the developer's approval. Order is
fixed: make the **plugin** current (steps 1–2), then bring the
**application** to the plugin's version (steps 3–8).

## Step 1 — Is this plugin itself up to date?

The plugin's version is its `VERSION` file:
`${CLAUDE_PLUGIN_ROOT}/VERSION` in Claude Code, else two directories
above this `SKILL.md`. Compare it with PyPI's latest `reboot`:

```bash
curl -fsSL --max-time 5 https://pypi.org/pypi/reboot/json |
    python3 -c 'import json, sys; print(json.load(sys.stdin)["info"]["version"])'
```

PyPI unreachable: say so and continue with step 3 (`VERSION` is still a
valid, if possibly stale, target).

## Step 2 — If the plugin is out of date, update it first

If PyPI is newer, update the plugin **before** touching the app — the
new release's migration notes and matching skills arrive only with it.
The developer performs the update and restart:

1. Re-run the installer (in Claude Code,
   `claude plugin update reboot@reboot-plugin` is equivalent):

   ```bash
   curl -fsSL https://reboot.dev/install.sh | bash
   ```

2. Restart the agent session so the updated plugin loads.
3. Run this skill again.

Stop here.

## Step 3 — Determine the application's current version

Project root: the directory (user-named or current) containing
`.rbtrc`. Current version is the app's pin:

- Python: the exact `reboot` pin in `pyproject.toml`.
- Node.js: the `@reboot-dev/reboot` version in `package.json`.

The **target** is exactly the plugin's `VERSION`, never "latest on
PyPI" — a newer release may need migration steps this plugin doesn't
know.

## Step 4 — Compare

- **Current == target:** report it's up to date. Stop.
- **Current > target:** do NOT downgrade; update the plugin (step 2).
  Stop.
- **Current < target:** proceed.

## Step 5 — Plan, and confirm with the developer

Read every fragment (`.md`) in this skill's `migrations/<version>/`
directories with current < `<version>` ≤ target, in ascending version
order (the order they apply). A version with no directory needs no code
migrations. Each fragment's front matter says which apps it touches:
skip one whose `applies` doesn't list this app's front door, or whose
`when` doesn't hold for it (check, don't assume). Tell the developer the
from/to versions and each remaining fragment's `summary`, plus the
skipped ones and why; get their go-ahead before changing anything.

## Step 6 — Apply the code migrations

Apply the fragments in ascending version order. If one asks for the
developer's input (e.g. which feature a test belongs to), ask and finish
it before the next. Code changes only — don't bump pins or regenerate
yet, so an interrupted upgrade still pins the old version, the mismatch
check fires next run, and this skill can be rerun.

## Step 7 — Bump every pin, once, to the exact target version

- `pyproject.toml`: every exact `reboot` pin, incl. `reboot[dev]` and
  any other dev dependency on it.
- `package.json`: every `@reboot-dev/*` dependency with an exact version
  (leave `workspace:*` alone).
- `Dockerfile` (if present): the `ghcr.io/reboot-dev/reboot-base` tag in
  `FROM`.

## Step 8 — Reinstall, regenerate, test

From the project root:

1. `uv sync` (Python) or the project's package manager (Node.js).
2. `rbt generate`.
3. Run the tests; fix upgrade-caused failures, guided by the migration
   notes.

## Step 9 — Report

Summarize the version change, migration steps applied (if any), and test
results.
