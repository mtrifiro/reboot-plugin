---
id: port-meridian-05
project: port-meridian
source: "v 1.4.1 Reboot/port-meridian/docs/reboot-learnings 04.md §3"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/agent-pydantic-ai.md
tags: [negative-space, testing]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "python/references/testing-project-setup.md § Do this"
---

# reboot.agents.pydantic_ai.Agent needs ANTHROPIC_API_KEY at import

**What happened.** `reboot.agents.pydantic_ai.Agent` requires `ANTHROPIC_API_KEY` to exist at module import (provider construction), even if no call is ever made. Offline and dev environments need a placeholder plus an app-level gate.

**Expected.** Not recorded.

**Repro.** Import a module that constructs an `Agent` at module scope with `ANTHROPIC_API_KEY` unset.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/testing-project-setup.md` § Do this: a `conftest.py` with `os.environ.setdefault("ANTHROPIC_API_KEY", "test-placeholder")` for "an LLM client built at import". `agent-pydantic-ai.md` § Do this constructs the `Agent` at module scope with the key from `ANTHROPIC_API_KEY` but does not say the key is needed at import; the offline `rbt dev run` case (placeholder plus app-level gate) is not covered.
