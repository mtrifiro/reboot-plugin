---
id: reboot-air-141-load-02
project: reboot-air-141-load
source: "reboot-air/REBOOT_LOAD_TEST_FINDINGS.md Finding 2"
reboot_version: 1.4.1
severity: red
target: plugin
names:
  - python/references/servicer-transaction.md
  - inspect/SKILL.md
tags: [negative-space, operations, error-text, cost]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Caller that disappears mid-transaction wedges the actor permanently

**What happened.** App under test: Reboot Air, a web app with six state types (`Airline`, `Airport`, `Plane`, `Flight`, `Booking`, `User`) and `Application(oauth=OAuthProviderByEnvironment(dev=Development(...)))`; `User.book` is a Transaction that takes exclusive locks on at least the `User` and the `Flight`. A separate load-driver process (one `ExternalContext` per virtual user, real sign-in through `/__/oauth/*`) ran 8 virtual users for 20 seconds, about 10% book-then-cancel, then cancelled its worker tasks. Four of five `Development()` accounts were fine; the fifth (worker 0's; workers 0 and 5 shared it) could not sign in, hung until the HTTP client timed out and still hung ten minutes later (`Alice: ReadTimeout 6.00s`, the others ok in 0.02-0.03s). Backend log: `reboot.aio.aborted.SystemAborted: aborted with 'Unavailable': Timed out waiting 30.0s to acquire exclusive lock; retry the transaction.` The exclusive lock the abandoned `book` held was never released. A restart cleared it immediately (Alice signed in again in 0.13s). It takes down sign-in because Reboot's OAuth server calls `set_claims` (a write) on the `User` actor during token exchange; the hang is on the `/__/oauth/callback` hop, far from `User.book`. It does not heal: no visible lease expiry, reaper, or rollback; the 30s is the waiter's wait, not a bound on the holder. No reference says what happens when a caller vanishes. Those who hit it: load generators, timing-out integration tests, cancelled CI jobs, Ctrl-C; the tool that caused it will refuse to start against the account it broke. The driver was changed to drain (set a stop flag, wait for in-flight calls, cancel only overruns, with a warning). Source severity: high.

**Expected.** In order of value: (1) release locks when the caller's channel closes (abort the transaction and admit the next writer); (2) failing that, a holder-side lease; (3) one paragraph in the transaction reference ("a transaction whose caller disconnects holds its lock until the application restarts; do not cancel in-flight calls"); (4) `rbt inspect` showing which actors hold locks and for how long.

**Repro.** 1. Any Reboot app with a Transaction that writes a `User` actor, and `Application(oauth=...)` so sign-in calls `set_claims`. 2. Drive that transaction concurrently from an `ExternalContext` in a separate process. 3. `task.cancel()` the callers mid-flight (or SIGINT the process). 4. Try to sign in as the affected identity; it hangs indefinitely. 5. Restart the application; it works again.

**Where in the skills.** `python/references/servicer-transaction.md` (paragraph requested); `inspect` skill (lock visibility). Companion to `reboot-air-141-21`.

**Checked at 1.6.0.** Still absent. `python/references/servicer-transaction.md` has no text about disconnected callers or retained locks (grep for disconnect / vanish / cancel found nothing relevant) and `inspect/SKILL.md` has no lock inspection.
