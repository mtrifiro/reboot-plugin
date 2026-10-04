---
id: tool-checks-03
project: tool-checks
source: "tools/check-symbols.py, 2026-10-04"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - python/references/stdlib-presence.md
tags: [version-drift, frontend]
cluster: "A"
still_applies: yes
status: Open
resolved_by: ""
---

# `stdlib-presence.md` gives the React hooks a Python-style module path

**What happened.** "React Hooks Live in `reboot.std.react.presence`".
There is no such Python module, and the text does not give the npm
package or import path a `.tsx` file would use.

**Expected.** The TypeScript import path for the presence hooks.

**Repro.** `import reboot.std.react.presence` → `ModuleNotFoundError`.

**Where in the skills.** `python/references/stdlib-presence.md:86-90`.

**Checked at 1.6.0.** Found by `tools/check-symbols.py`. The correct npm
path was not determined.
