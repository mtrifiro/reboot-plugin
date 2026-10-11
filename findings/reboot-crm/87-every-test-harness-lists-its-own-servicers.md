---
id: reboot-crm-87
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.6"
reboot_version: 1.6.0
severity: red
target: framework
names:
  - python/references/testing-harness.md
tags: [testing, scaffold, pattern]
cluster: "B"
still_applies: unknown
status: Resolved
resolved_by: "python/references/lifecycle-application-entry.md § One list for the application and every test; python/references/testing-harness.md § Limits"
---

# Every test harness lists its own servicers

**What happened.** Adding the `Spend` type meant editing six `Application(servicers=[...])` lists (`research_test`, `chat_test`, `web_test`, `importing_web_test`, `poggio_test`, `backend_world`). The same drift once broke every lead import (a servicer missing from the list fails at call time with `Method not found!`, see P1.17). `backend_world.py` was meant to be the one list but modules needing a scripted provider or an `initialize` built their own. Status: done 2026-10-04: `backend/src/servicers/registry.py` is the one list; `main.py` and all six harnesses take `SERVICERS` and `libraries()` from it.

**Expected.** One `servicers()` in `tests/` that every harness takes. For Reboot: an `Application` that registers every servicer in a package by default (or `rbt` generating the list), so a new type cannot be left out.

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-harness.md` (lists servicers inline per example).

**Checked at 1.6.0.** `python/references/testing-harness.md` (lines ~56, 89) shows per-test inline servicer lists; no shared-registry guidance.
