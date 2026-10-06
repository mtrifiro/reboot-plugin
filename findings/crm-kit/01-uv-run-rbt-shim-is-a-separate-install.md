---
id: crm-kit-01
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §1"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-rbtrc.md
  - run/SKILL.md
tags: [operations, negative-space]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# The bare rbt shim runs a separate Reboot install from the project venv, so patches to one do nothing for the other

**What happened.** The app runs on the interpreter of the `rbt` that started it (`dev.py`: `launcher = sys.executable`). `uv run rbt` uses the project `.venv`. The bare `rbt` is the plugin shim, which `exec`s `uvx --from=reboot==1.6.0 --python=3.12` and runs a separate copy under `~/.cache/uv/archive-v0/<hash>/.../site-packages/reboot/`; patching one copy does nothing for the other. Calling `.venv/bin/rbt` directly fails: `Failed to find 'protoc-gen-reboot_python'`. Rule adopted: always invoke the CLI as `uv run rbt ...` from the project root, so there is one install to patch; if the bare shim is ever used (e.g. `rbt generate` without `uv run`), patch its copy too by running the patch script through `"$(dirname "$(command -v rbt)")/uvx" --from=reboot==1.6.0 --python=3.12 python -`, with versions from `grep -E '^(REBOOT|PYTHON)_VERSION=' "$(command -v rbt)"`.

**Expected.** Always `uv run rbt ...` from the project root (the source's rule).

**Repro.** Not recorded.

**Where in the skills.** Not named by the source; `python/references/lifecycle-rbtrc.md` and `run/SKILL.md` cover how `rbt` is invoked.

**Checked at 1.6.0.** `python/references/lifecycle-rbtrc.md` § Errors you will see and `errors.md` list `Failed to find 'protoc-gen-reboot_python'` with the fix `uv run rbt ...`; nothing under `skills/` says the bare shim runs a separate `uvx` copy of `reboot` from the venv's (grep `uvx`, `shim`, `archive-v0`).
