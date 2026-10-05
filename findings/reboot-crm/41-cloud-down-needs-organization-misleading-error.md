---
id: reboot-crm-41
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.7b"
reboot_version: 1.6.0
severity: yellow
target: cloud
names:
  - python/references/lifecycle-reboot-cloud.md
  - deploy/SKILL.md
tags: [operations, error-text, contradiction]
cluster: "4.4"
still_applies: yes
status: Resolved
resolved_by: "python/references/lifecycle-reboot-cloud.md § Never; deploy/SKILL.md § Step 2 — Deploy the backend to Reboot Cloud"
---

# rbt cloud down needs --organization, and says the application does not exist when it is missing

**What happened.** `rbt cloud down --application-name=<app> --expunge` answered "User '<uuid>' does not have an application named '<app>'. If the application belongs to an organization, try adding --organization=<name>." The application did exist; the sentence leads with a false statement and invites the conclusion that a previous command destroyed it. `rbt cloud down --help` lists `--organization` as optional. The project's own `DEPLOYING.md` already records that every `rbt cloud up` needs `--organization`, first deploy or not, whereas the plugin's reference says it is only required once.

**Expected.** Either the flag is genuinely optional for an application the key can see, or `--help` marks it required and the error says "missing --organization" instead of denying the application exists. Recommendation: fix the message before the flag.

**Repro.** `rbt cloud down --application-name=<an app you own> --expunge` with `REBOOT_CLOUD_API_KEY` set and no `--organization`.

**Where in the skills.** `python/references/lifecycle-reboot-cloud.md` (~lines 77-79), `deploy/SKILL.md` line ~51.

**Checked at 1.6.0.** `lifecycle-reboot-cloud.md` lines 77-78 still say `--organization` is required only the first time an app is created.
