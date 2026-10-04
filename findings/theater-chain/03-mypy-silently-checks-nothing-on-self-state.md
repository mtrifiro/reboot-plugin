---
id: theater-chain-03
project: theater-chain
source: "theater-chain/reboot-findings.md §3"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/lifecycle-project-setup.md
tags: [testing, negative-space, scaffold]
cluster: "8.4"
still_applies: yes
status: Open
resolved_by: ""
---

# mypy silently checks nothing on self.state and the smoke test misses it

**What happened.** `lifecycle-project-setup.md` gives a `.mypy.ini` and says to confirm it is live by adding a bogus attribute access on a state model and checking mypy reports `has no attribute`. The author did exactly that and mypy reported nothing, with a correct `.mypy.ini` and a green build. The cause is codegen, not config: generated `<name>_rbt.py` has `State: IMPORT_typing.TypeAlias = IMPORT_typing.cast(type, IMPORT_api.Chain.state)` (and the same for `CreateRequest`, and every `<Type>.<Method>Response`), and `typing.cast(type, ...)` is opaque to mypy so they widen to `Any`. Since `self.state` is annotated `-> Chain.State`, every field access and request field in every servicer is unchecked. `reveal_type` shows `Revealed type is "Any"` for `Chain.State` versus the hand-written `theater.v1.theater.ChainState`. Typed errors are generated properly (`caught.exception.error` is a real 28-member union). Workaround, two lines per servicer: bind the hand-written pydantic classes yourself, e.g. `@property def show(self) -> ShowingState: return self.state` and `req: HoldSeatsRequest = request`, after which mypy reports errors like `"ShowingState" has no attribute "seatsTYPO"`.

**Expected.** (a) Replace the misleading verification recipe in `lifecycle-project-setup.md` with the `reveal_type` check and the typed-local workaround. (b) Framework: emit `State: TypeAlias = ChainState` (a real import of the user's class) instead of `cast(type, ...)`; the source calls this the highest-leverage change available to the framework.

**Repro.** Add a bogus attribute access on a state model and run mypy; it reports nothing. `reveal_type(self.state)` shows `Any`.

**Where in the skills.** `python/references/lifecycle-project-setup.md`.

**Checked at 1.6.0.** Still present. `python/references/lifecycle-project-setup.md:194-195` still recommends the bogus-attribute check; no `reveal_type` or `cast(` text found.
