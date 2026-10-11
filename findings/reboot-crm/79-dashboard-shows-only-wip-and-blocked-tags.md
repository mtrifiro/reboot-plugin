---
id: reboot-crm-79
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P4.10"
reboot_version: 1.6.0
severity: green
target: framework
names:
  - python/references/testing-features.md
  - feature/SKILL.md
tags: [testing, operations]
cluster: "8.4"
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-features.md § Limits"
---

# The dashboard marks and filters two tags; a suite's own tags are invisible there

**What happened.** The suite tags scenarios with its own tiers (`@critical` 47, run before every commit; `@important` 52, before a deploy) and marks one feature `@dormant`. pytest-bdd turns every tag into a mark so `-m critical` works. The dashboard marks `@wip` green and `@blocked` red and filters by those two only, so it cannot answer "which scenarios guard every commit?". Workaround: copy `@wip` onto the tier while reviewing, then take it off (see reboot-crm-96).

**Expected.** Show every tag on a feature, rule and scenario and let the filter take any of them or a pytest `-m` expression; keep `@wip` and `@blocked` coloured, others plain chips (recommendation: do it).

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-features.md` "Tags: `@wip` and `@blocked`".

**Checked at 1.6.0.** `python/references/testing-features.md` (lines ~281-313) still says the dashboard marks and filters only `@wip` and `@blocked`.
