---
id: reboot-crm-81
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P4.12"
reboot_version: 1.6.0
severity: green
target: bdd
names:
  - python/references/testing-web-app.md
tags: [testing, frontend]
cluster: "4.1"
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-web-app.md § Never"
---

# opens the web app at takes its path as written, while every other web step recalls saved values

**What happened.** A browser scenario saved an imported lead's id as "bea lead" and opened `"/l/<bea lead>"`. The page loaded a lead that does not exist and the scenario failed two steps later on text it could not find; nothing said the path had not been filled in. `reboot/bdd/web.py` passes the path straight to `web_app.open`, where click, fill and sees steps beside it run quoted text through `_with_saved` first. Workaround: reach the page the way a person does (open the list, click the row, follow the link).

**Expected.** The same recall in the path as in every other quoted argument of the web steps, or the step's docstring saying it has none.

**Repro.** Save any id, then `"alice" opens the web app at "/x/<that id>"`.

**Where in the skills.** `python/references/testing-web-app.md` (step table).

**Checked at 1.6.0.** `python/references/testing-web-app.md` line ~156 says quoted text may say `<name>` for saved values but does not exclude or confirm the `opens the web app at` path.
