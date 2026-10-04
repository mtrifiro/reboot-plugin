---
id: reboot-air-150-05
project: reboot-air-150
source: "reboot-air/reboot-findings.md §5"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/servicer-writer.md
  - python/references/scheduling-recurring.md
  - python/references/state-collections.md
tags: [contradiction, pattern, negative-space]
cluster: "8.4"
duplicate_of: theater-chain-01
still_applies: yes
status: Open
resolved_by: ""
---

# Persisting wall-clock values from writers/transactions passed effect validation; the plugin says it shouldn't

**What happened.** `servicer-writer.md` and `scheduling-recurring.md` say: "What to avoid is persisting a wall-clock or random value into `self.state` from a writer: writer bodies re-execute under transient retries and dev-mode effect validation, so a stored non-deterministic value would differ across runs." The app's `User.add_to_cart` (a Transaction) reads `datetime.now()`, passes it to `Flight.hold` and stores the returned `hold_expires_at` in the cart; `User.checkout` stores `purchased_at` from the clock into a new `Order`. `state-collections.md` itself shows `self.state.people_index_id = str(uuid4())` inside a `create` Writer. The harness (effect validation on by default) logged `Re-running method ... to validate effects` for every writer and transaction and never flagged a mismatch across 13 tests. Resolved by docs.reboot.dev/learn_more/side_effects: validation "always executes your Reboot methods twice" in development as a reminder that external calls must be able to execute at least twice; the docs never claim a determinism comparison of mutations, which exists only in the plugin's `servicer-writer.md` / `scheduling-recurring.md`.

**Expected.** The skill text should match the docs. Remaining ask: the recommended pattern for "a hold expires two minutes from now" (a timestamp has to be persisted somewhere): if the answer is "pass `now` in from the outermost call and treat it as request data", show it; if wall-clock reads in a writer are fine, soften the warning.

**Repro.** Not recorded.

**Where in the skills.** `servicer-writer.md`, `scheduling-recurring.md`, `state-collections.md`.

**Checked at 1.6.0.** `python/references/servicer-writer.md` (lines ~28-31, "re-runs the body and asserts the state mutations match") and `scheduling-recurring.md` (lines ~198-203) still carry the determinism claim; `state-collections.md` still shows `uuid4()` in a constructor.
