---
id: client-portal-12
project: client-portal
source: "client-portal/reboot-findings.md §12"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - feature/SKILL.md
  - dashboard/SKILL.md
  - python/references/testing-features.md
tags: [testing, negative-space]
cluster: "8.4"
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-features.md § Never; feature/SKILL.md § Step 4 — Iterate on the scenarios with the user"
---

# The feature files run, but the rules they carry mostly do not (a Rule: with no Scenario: stays green)

**What happened.** `tests/` holds two modules and `uv run pytest` passes (`26 passed in 204.70s (3:24)`): `portal_test.py` wires five of the six feature files through `reboot.bdd`'s `scenarios(...)` against a real `Application`, and `obsidian_test.py` holds 13 unit tests of the vault rules. What is missing is a scenario for most of what the session learned. A `Rule:` with prose and no `Scenario:` beneath it is read by the developer and the dashboard and by nothing else; several of the bugs in this file were already written down as rules before they bit ("Two sync passes over one portal never overlap") and passed a green suite while false. The work left is scenarios under the rules: overlap and the claim, the stale-pass stand-down, the publish gate with the flag on and off, hidden paths, and a contents tree that prunes branches leading nowhere. Cost note: the suite takes three and a half minutes for 26 tests, most of it spent bringing applications up.

**Expected.** Scenarios under the rules, not a better harness.

**Repro.** Not recorded.

**Where in the skills.** `feature/SKILL.md` step 2 (scenario writing) and the dashboard.

**Checked at 1.6.0.** `feature/SKILL.md` has no lint or check for a `Rule:` without a `Scenario:`.
