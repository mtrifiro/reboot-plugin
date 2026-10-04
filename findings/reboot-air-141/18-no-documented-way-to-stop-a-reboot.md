---
id: reboot-air-141-18
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §19"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - run/SKILL.md
tags: [operations, error-text]
cluster: "F"
duplicate_of: reboot-crm-15
still_applies: yes
status: Open
resolved_by: ""
---

# No documented way to stop a Reboot app and the obvious one leaves orphans

**What happened.** `run/SKILL.md` is the canonical start procedure and says nothing about stopping. `rbt dev run` spawns children whose command line is `python <project>/backend/src/main.py`, not `rbt dev run`, so `pkill -f "rbt dev run"` kills the supervisor and leaves the children. Over a session the author found fifteen orphaned `main.py` processes, the oldest three hours old, still holding state. Two failures resulted: (1) after an expunge and restart an older orphan still bound `:9991` and re-seeded the database with pre-edit code, so a schedule change "didn't take" and was chased as a data bug; (2) a later start died at boot with `grpc.aio._call.AioRpcError: StatusCode.UNIMPLEMENTED details = "Method not found!"` from `validate_schema_backwards_compatibility` -> `get_application_metadata`, which reads like a framework bug and really means an incompatible older process is alive.

**Expected.** A "Stopping the app" section in `run/SKILL.md` with a pattern matching the children (e.g. `pkill -f "<project>/backend/src/main.py"` and `pkill -f "rbt dev run"`), a note that a leftover process shows as a stale-state mystery or `UNIMPLEMENTED / Method not found!` at boot, and a pointer to `rbt dev stop` if one ever exists.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md`.

**Checked at 1.6.0.** Still absent. `run/SKILL.md` has no stop/pkill/orphan/expunge/lsof section (grep found only an unrelated "not stop after one" line at 234).
