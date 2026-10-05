---
id: reboot-air-141-04
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §4"
reboot_version: 1.4.1
severity: green
target: plugin
names:
  - web-app/SKILL.md
tags: [scaffold]
cluster: "4.2"
still_applies: unknown
status: Resolved
resolved_by: "build/SKILL.md § Step 1 — API definition; build/SKILL.md § Step 2 — Project shell"
---

# mypy.ini step precedes the API decision it depends on

**What happened.** Build-flow step 1 says to write `.mypy.ini`; step 3 says to write the API definition. But `.mypy.ini` needs a `[mypy-<pkg>.v1.<name>_rbt]` stanza naming the API module that does not exist yet, so step 1 can only be completed by having already decided step 3's package and file name. The design phase does front-load that decision, but an agent following steps literally will write a placeholder stanza and forget to return. Cost: minor.

**Expected.** One clause in step 1: name the ignore stanza after the API module settled on in the design phase.

**Repro.** Not recorded.

**Where in the skills.** `web-app/SKILL.md`, Step-by-Step Build Flow, steps 1-3.

**Checked at 1.6.0.** Step order is unchanged in `web-app/SKILL.md` (step 1 writes `.mypy.ini`, step 4 writes the API definition, lines 524-542), but whether the stanza is still required was not verified.
