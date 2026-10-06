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
status: Resolved
resolved_by: "python/references/lifecycle-rbtrc.md § Limits; run/SKILL.md § Before starting: is the port free?"
---

# --port on the command line is refused when .rbtrc sets it

**What happened.** `.rbtrc` pins `dev run --port=9989`. Starting a second instance from another checkout with `uv run rbt dev run --no-chaos --port=9979` fails: `rbt dev run: error: the flag '--port' was set multiple times; it can only be set once, including in the `.rbtrc` file`. The `.rbtrc`'s own comment assumes the command line wins for another flag (`--size` on `rbt cloud up` overrides it), so the file is inconsistent with itself. Two instances is the ordinary case for a second branch or reviewer; the only way is to edit a tracked file. Seen again 2026-10-05 with a second Cloud application: adding a staging app meant `rbt cloud up` naming two applications at two sizes. With `--application-name` and `--size` pinned in `.rbtrc`, passing the staging values on the command line risked the same refusal, so both lines came out of `.rbtrc` and `scripts/deploy.sh` passes them per environment; the pin that kept a redeploy from silently changing size now lives in a script instead of the file every `rbt` command reads. Retiring staging the same day hit one more gap: `rbt cloud down --no-expunge` is refused ("Currently all applications brought down are expunged", reboot-dev/reboot#71), so an application cannot be stopped with its state kept; stopping it is deleting it.

**Expected.** The command line beats the config file for every flag, or the error says a flag cannot be overridden rather than treating a command-line value as a duplicate.

**Repro.** Pin `--port` in `.rbtrc`, then pass `--port` on the command line.

**Where in the skills.** Not applicable to a skill (CLI behaviour); `python/references/lifecycle-rbtrc.md` documents `.rbtrc` generally.
