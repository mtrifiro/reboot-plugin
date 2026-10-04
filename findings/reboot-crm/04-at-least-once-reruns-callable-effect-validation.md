---
id: reboot-crm-04
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P0.4"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/servicer-workflow.md
  - python/references/testing-failure-recovery.md
  - python/references/testing-features.md
  - python/references/agent-pydantic-ai.md
  - python/references/agent-tools.md
tags: [negative-space, cost, testing, contradiction]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# at_least_once re-runs its callable to validate effects and keeps the second value; no skill mentions the per-call opt-out

**What happened.** Corrected by the author after the Reboot team pushed back: the doubling of paid calls is not a whole-workflow re-run, it is `at_least_once` itself. In `reboot/aio/memoize.py`, `callable_validating_effects()` awaits `callable()` and then, unless the call is `at_most_once`, an `until`, or effect validation is disabled, restores the context checkpoint and awaits `callable()` again; the memoized value is the second one. Both invocations occur inside one `memoize` call before anything commits, so no application guard can see the second request (a claim write at the top of the workflow measured 2 raw calls per ask in both shapes). `memoize.py` carries a TODO about not checking whether the two results differ. The opt-out exists per call: `at_least_once(..., effect_validation=EffectValidation.DISABLED)`, whose docstring names the case (callables that are intentionally non-deterministic or expensive, e.g. LLM requests). Measured 2026-09-22: before, `1 asks, 2 raw calls` at every ask; after passing the argument at the Perplexity and assistant call sites (four servicers), `1 asks, 1 raw calls`, 21 research and 23 chat scenarios passing; effect validation stays on elsewhere. The earlier entry's claim that `.rbtrc` `dev run --effect-validation=disabled` is the only remedy was false. A test double that pops answers off a list changes behaviour silently under the second-wins rule; the app's rule is that a stand-in derives its answer from its input, never from a counter.

**Expected.** Documentation changes the source asks for: (a) runtime log a WARNING when the two invocations return different values; (b) name the remedy and the second-result-wins rule in the `Re-running block ... to validate effects` log line; (c) `servicer-workflow.md` (before the Stripe example) documents that in development the callable runs twice, the second result is memoized, and `effect_validation=EffectValidation.DISABLED` is the per-call switch, preferred over the application-wide `.rbtrc` setting; (d) `agent-pydantic-ai.md` and `agent-tools.md` say their no-re-billing promise covers replay, not effect validation; (e) `testing-features.md` and `testing-failure-recovery.md` mention the per-call argument and the pure-stand-in rule beside the `call_count == 2` example; (f) one clause on the method re-run log line; (g) the still-waiting-after-re-run warning should be info. Source recommendation: the documentation items are the whole finding; (a) is a minor runtime improvement.

**Repro.** Put a billed or non-deterministic call inside `at_least_once` in a workflow under `rbt dev run` or the test harness and count raw calls.

**Where in the skills.** `python/references/servicer-workflow.md` (~line 640), `agent-pydantic-ai.md` (~19), `agent-tools.md` (~16), `testing-features.md` (~383), `testing-failure-recovery.md` (~167).

**Checked at 1.6.0.** `effect_validation=` appears only in `python/references/testing-failure-recovery.md` line 183 (the harness-wide form); no reference documents it as a per-call argument on `at_least_once`/`at_most_once`, and `agent-pydantic-ai.md` still promises no re-billing on replay.
