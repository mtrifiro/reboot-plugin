---
id: mattprd-03
project: mattprd
source: "2026.08.22 REBOOT_FINDINGS.md §3"
reboot_version: 1.4.1
severity: yellow
target: plugin
names:
  - run/SKILL.md
  - python/references/lifecycle-rbtrc.md
tags: [error-text, version-drift, operations]
cluster: "4.4"
still_applies: yes
status: Resolved
resolved_by: "python/references/lifecycle-rbtrc.md § Errors you will see; run/references/stop-restart-reset.md § Errors you will see"
---

# 'Address already in use' is reported as an internal Reboot/Envoy bug; run skill names a nonexistent port knob

**What happened.** Starting `rbt dev run` while another Reboot app held port 9991 printed: `Error adding/updating listener(s) public: cannot bind '0.0.0.0:9991': Address already in use` followed by 'This is a bug in the Envoy configuration Reboot generated ... please report this bug to the maintainers.' The message claims it is a Reboot bug, asks to report it, and never mentions the fix (`dev run --port=<other>`). Related doc gap: the `run` skill points at 'the `application_port` knob in `lifecycle-rbtrc.md`' for changing the port, but that reference contains no such knob; `--port` was discovered via `rbt dev run --help`.

**Expected.** Runtime special-cases EADDRINUSE on the public listener (names the port and likely cause, prints the `--port` fix). Update `lifecycle-rbtrc.md` (or the `run` skill pointer) to document `dev run --port=`.

**Repro.** Not recorded.

**Where in the skills.** `run` skill, `lifecycle-rbtrc.md`.

**Checked at 1.6.0.** run/SKILL.md:130-132 still says 'see python/references/lifecycle-rbtrc.md for the `application_port` knob'; grep `application_port` finds no definition in lifecycle-rbtrc.md. `--port` appears only in dashboard/SKILL.md:100 (dashboard port).
