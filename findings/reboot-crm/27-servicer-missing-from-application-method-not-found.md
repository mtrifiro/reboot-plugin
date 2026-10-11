---
id: reboot-crm-27
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.17"
reboot_version: 1.6.0
severity: red
target: framework
names:
  - python/references/testing-harness.md
tags: [negative-space, error-text, testing]
cluster: "4.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-harness.md § Errors you will see"
---

# A servicer missing from Application(servicers=[...]) fails at call time, saying Method not found!

**What happened.** A new state type with a servicer was added to the API and registered in `backend/src/main.py`; six test harnesses build their own `Application(servicers=[...])` and were not updated. Each application started cleanly, served every other type, and the first scenario touching the new type aborted with `grpc.aio._call.AioRpcError: status = StatusCode.UNIMPLEMENTED details = "Method not found!"` on a method that exists, on a type that exists. The text is identical to the start-up race described in reboot-crm-18, so a developer cannot tell a forgotten servicer (one-line fix) from a placement client that has not converged (framework race); the only discriminator was that one was deterministic.

**Expected.** An application whose API declares a `Type` that `servicers=` does not implement is misconfigured at construction and should be refused at `Application(...)` naming the type (as a missing `libraries=` entry for `OrderedMap` is). Failing that, make the transport distinguish "no such method" from "no servicer for this type in this application", or at least reword `Method not found!`. The source calls it the highest-traffic misleading error in the file.

**Repro.** Declare a `Type` in the API, omit its servicer from `Application(servicers=[...])`, start the application (it starts), and call any method on that type.

**Where in the skills.** No skill row for this error exists (error-index candidate).

**Checked at 1.6.0.** No skill text under `skills/` mentions `Method not found!` (grep).
