---
id: plugin-browser-06
project: plugin-browser
source: "plugin-browser/FINDINGS.md § Plugin skills, item 4"
reboot_version: 1.6.0
severity: yellow
target: plugin
names: []
tags: [operations]
cluster: ""
still_applies: no
status: Obsolete
resolved_by: ""
---
# The Reboot band reports deploys that never ran

**What happened.** The band (`mods/reboot-progress`) took any command output containing a `….pages.dev` address as a deploy result, and any command whose text contained `rbt cloud up` as a deploy starting. Printing another app's deploy guide put that app's Site button on this session's band; writing tests that contain `rbt cloud up` showed "Deploying to Reboot Cloud: revision is starting up" with nothing deployed.

**Expected.** Only a command that runs `rbt cloud up`, `wrangler pages deploy` or `scripts/deploy.sh`, or output while such a deploy runs, counts.

**Repro.** `cat` a doc mentioning `https://x.pages.dev`; or run a command whose text contains `rbt cloud up` without running it.

**Where in the skills.** `mods/reboot-progress/hooks/` (`deploy.ts`: `deployProgram()`, `isDeployCommand()`). Fixed since in `a40cfe5` and `9ee13e6`, so Obsolete.
