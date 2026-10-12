---
id: hotel-7-01
project: hotel-7
source: "hotel-7/FINDINGS.md § Plugin skills, item 1"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/lifecycle-rbtrc.md
  - mcp-ui/references/project-shell.md
tags: [operations, negative-space]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# The `.rbtrc` reference never says `rbt dev run` also restarts on API changes, so the build told the user it doesn't

**What happened.** Asked how the backend reloads itself, the build (main's plugin, Claude app, 2026-10-12) explained `dev run --watch=backend/**/*.py` correctly, then said: "One gap in that setup: the watch covers `backend/` only, not `api/`. If you change the API definition in api/hotel/v1/hotel.py, run `uv run rbt generate` or restart the backend tab yourself. I can add `dev run --watch=api/**/*.py` to `.rbtrc`." That is wrong. `rbt dev run` takes `--generate-watch`, default true, which runs `rbt generate --watch` in the background from the `.rbtrc` `generate` lines, and it watches the API definitions itself (`proto_globs` in `reboot/cli/commands/dev.py`). An edit under `api/` regenerates `backend/api/`, which the `--watch` glob covers, so the backend restarts. It also restarts when `.rbtrc` or the `--env-file` changes.

**Expected.** The reference that teaches the `--watch` lines to say what else triggers a restart: API definitions (through `--generate-watch`), `.rbtrc` and the env file. It should also say that a change that breaks the API (a removed field, even on a response) makes `rbt dev run` stop and wait instead of restarting. Without that, the build guesses and offers a redundant `--watch=api/**` line.

**Repro.** In a project made from the template, ask the build "how does the backend reload itself?". Read `reboot/cli/commands/dev.py`, `--generate-watch` and the `protos_event_task` / `have_rc_file_or_protos_or_watch_event` loop.

**Where in the skills.** `python/references/lifecycle-rbtrc.md`, the "Correct" `.rbtrc` block and its comments (mentions `--watch` and that `--env-file` edits restart, nothing on API changes or `--generate-watch`); `mcp-ui/references/project-shell.md` line 42.

**Checked at import (2026-10-12).** Partly there: `lifecycle-rbtrc.md` § Do this says the default `--generate-watch` re-runs `rbt generate` and that `.rbtrc` and `--env-file` edits restart the app, but not that an `api/` edit therefore restarts it, and its own example block still carries `dev run --watch=api/**/*.py` ("keeps reloads under `--no-generate-watch`"), which is the line the build offered. Nothing there points to `api-schema-evolution.md` for the stop-and-wait on a breaking change (plugin-browser-09 is that case).
