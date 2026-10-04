---
id: reboot-crm-24
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.14"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - python/references/lifecycle-rbtrc.md
tags: [operations, error-text]
cluster: "F"
still_applies: unknown
status: Open
resolved_by: ""
---

# --port on the command line is refused when .rbtrc sets it

**What happened.** `.rbtrc` pins `dev run --port=9989`. Starting a second instance from another checkout with `uv run rbt dev run --no-chaos --port=9979` fails: `rbt dev run: error: the flag '--port' was set multiple times; it can only be set once, including in the `.rbtrc` file`. The `.rbtrc`'s own comment assumes the command line wins for another flag (`--size` on `rbt cloud up` overrides it), so the file is inconsistent with itself. Two instances is the ordinary case for a second branch or reviewer; the only way is to edit a tracked file.

**Expected.** The command line beats the config file for every flag, or the error says a flag cannot be overridden rather than treating a command-line value as a duplicate.

**Repro.** Pin `--port` in `.rbtrc`, then pass `--port` on the command line.

**Where in the skills.** Not applicable to a skill (CLI behaviour); `python/references/lifecycle-rbtrc.md` documents `.rbtrc` generally.
