---
id: new-crm-03
project: new-crm
source: "new-crm/docs/PATCHES.md §namespace package"
reboot_version: 1.6.0
severity: unrated
target: plugin
names: []
tags: [operations]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# In this install reboot imports as a namespace package, so a patch script using reboot.__file__ fails

**What happened.** In this project's install `reboot` imports as a namespace package, so the crm-kit's patch script, which locates the package with `pathlib.Path(reboot.__file__).parent`, does not work here; the project's version uses `pathlib.Path(list(reboot.__path__)[0])` instead. Same Reboot 1.6.0.

**Expected.** Locate the installed package with `reboot.__path__`, which works for a namespace package.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source; no skill carries a patch script.

**Checked at 1.6.0.** No skill under `skills/` locates the installed `reboot` package or documents either patch (grep `reboot.__path__`, `reboot.__file__`, `namespace package`).
