---
id: findings-board-06
project: findings-board
source: "findings-board/FINDINGS.md § reboot.bdd, item 5"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - python/references/testing-features.md
tags: [negative-space, testing]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-features.md § Layout and the test module"
mechanism: prose
---
# pytest-bdd drops hyphens from scenario names, so `-k` on the hyphenated word selects nothing

**What happened.** "The fix-owner filter …" becomes `test_the_fixowner_filter_…` and "A re-sync …" `test_a_resync_…`; `-k "fix_owner or re_sync"` ran six of eight new scenarios and reported no failure for the two it skipped. Workaround: check with `pytest --collect-only -q` before trusting a narrowed run, or avoid hyphens in scenario names.

**Expected.** `testing-features.md`, which suggests `-k "<scenario words>"`, to say how punctuation is folded.

**Repro.** A scenario named "The fix-owner filter …"; `uv run pytest -k fix_owner`.

**Where in the skills.** `python/references/testing-features.md` § Layout and the test module (the `-k "transfer between two"` example).
