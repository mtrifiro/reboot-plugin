---
id: tool-checks-02
project: tool-checks
source: "tools/check-symbols.py, 2026-10-04"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/stdlib-presence.md
tags: [version-drift]
cluster: "A"
still_applies: yes
status: Resolved
resolved_by: "python/references/stdlib-presence.md § Never"
---

# `stdlib-presence.md` names Python modules that do not exist

**What happened.** The reference labels `Subscriber` as
`reboot.std.presence.subscriber.v1.subscriber` and `MousePosition` as
`reboot.std.presence.mouse_tracker.v1.mouse_position`. Neither imports.
All three types (`Presence`, `Subscriber`, `MousePosition`) and their
servicers live in `reboot.std.presence.v1.presence`. The two labels look
like proto package names.

**Expected.** Label each type with the module an agent would import from.

**Repro.** `import reboot.std.presence.subscriber.v1.subscriber` →
`ModuleNotFoundError`; `from reboot.std.presence.v1.presence import Subscriber, MousePosition` works.

**Where in the skills.** `python/references/stdlib-presence.md:29,48`.

**Checked at 1.6.0.** Found by `tools/check-symbols.py`.
