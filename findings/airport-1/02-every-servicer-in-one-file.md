---
id: airport-1-02
project: airport-1
source: "airport-1/FINDINGS.md § Plugin skills, item 2"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - build/SKILL.md
  - build/templates/web-app/backend/src/servicers/__app__.py
  - build/templates/web-app/backend/src/servicers/registry.py
  - build/templates/README.md
  - python/references/lifecycle-application-entry.md
tags: [scaffold, pattern]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# The build puts every servicer in one file; nothing says to split by state type

**What happened.** The web-app template ships one servicer module, `backend/src/servicers/__app__.py`, and build Step 3 says "Write `backend/src/servicers/<app>.py`". Following it put six state types' servicers (Airport, GateSchedule, Flight, Day, Roster, User) in one 450-line file after the first prototype. The developer asked for one module per object, which meant a split and a rewrite of `registry.py` and `AGENTS.md` mid-build.

**Expected.** A layout that grows with the model from the first servicer: one module per state type, named for it in snake_case (`gate_schedule.py` for `GateSchedule`), each importing only what it uses; shared helpers in `servicers/common.py`; predicates in `servicers/auth.py`; `registry.py` importing one class per module. The API stays one package per domain, since a `Model` shared across API packages generates code that fails to import (`api-pydantic.md`, Limits).

**Repro.** Follow build Step 3 for any app with more than two state types.

**Where in the skills.** `build/SKILL.md` Step 3 ("Write `backend/src/servicers/<app>.py`") and Step 2a (the stubs); `templates/web-app/backend/src/servicers/__app__.py` and its `registry.py`; `templates/README.md` Files table; `python/references/lifecycle-application-entry.md` (the registry example imports from one `servicers.bank`). Suggested change: Step 3 reads "one module per state type, `backend/src/servicers/<type>.py`", the template names its sample module after its state type (`user.py`), and the template `AGENTS.md` row says "one module per state type".
