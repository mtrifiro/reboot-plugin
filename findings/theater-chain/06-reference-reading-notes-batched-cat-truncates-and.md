---
id: theater-chain-06
project: theater-chain
source: "theater-chain/reboot-findings.md §6"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/testing-harness.md
  - python/SKILL.md
tags: [index-gap, testing]
cluster: "G"
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-harness.md § Do this"
---

# Reference-reading notes: batched cat truncates and ExternalContext import

**What happened.** Four notes. (1) `cat`-ing several references at once can exceed the tool's inline output limit and get persisted to a file, never reaching context; read them one per call. The skill's "read each reference at the step that needs it" advice is right; the failure mode is batching, not volume. (2) `ExternalContext` is importable from `reboot.aio.external`, not `reboot.aio.contexts`; `testing-harness.md` uses the type without importing it. (3) `pyproject.toml` must not include `pytest-asyncio` (`testing-project-setup.md` says so; easy to add out of habit). (4) An `EmptyCartError` model with no fields (`pass`) generates and round-trips fine.

**Expected.** One line in `testing-harness.md` giving the `ExternalContext` import; per the proposal, a hook-reminder line to read one reference per tool call.

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-harness.md`; hook reminder.

**Checked at 1.6.0.** Still present for the main gaps. `python/references/testing-harness.md` has no `ExternalContext` import (no `reboot.aio.external` import for it anywhere in the skills; only `InitializeContext` at `python/SKILL.md:119`), and `hooks-handlers/remind.sh` has no read-one-reference-per-call line. The `pytest-asyncio` point is already covered at `python/references/testing-project-setup.md:121`.
