---
id: cineloop-34
project: cineloop
source: "cineloop/reboot-findings.md §24 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - inspect/SKILL.md
tags: [operations, error-text]
cluster: "F"
still_applies: no
status: Obsolete
resolved_by: ""
---

# 'Correct' and 'comprehensible' are different bars; rbt inspect needs the fully-qualified type name

**What happened.** A user opened a seat map and reported holding three seats not in their cart. Every layer behaved as designed (seats were really theirs, `rbt inspect` showed them `sold` under a real order; the cart really was empty; the map highlights the caller's seats), yet nothing on the page said 'bought'. Fixes: a check-mark glyph for bought seats where held seats show a number (a border difference is invisible at 24px) and a 'You have tickets here' panel listing seats, amount paid and receipt link. Lesson: when a screen shows state a user did not create in this session it must explain the state, not just render it. Also: `rbt inspect state get` on the showing and the order turned 'the UI looks broken' into 'the UI is correct and unclear' in under a minute, so use `rbt inspect` as the first debugging move. Practical note: pass the fully-qualified type name (`--type=cineloop.v1.Showing`, not `--type=Showing`) or it fails with `Unknown state type for state reference '<id>'`, which reads like the actor is missing. `rbt inspect type list` prints exact names.

**Expected.** Add to `inspect/SKILL.md` examples showing the `type list` then `state get` sequence together; note the error text.

**Repro.** Run `rbt inspect state get --type=Showing ...` with a short type name.

**Where in the skills.** `inspect/SKILL.md`.

**Checked at 1.6.0.** `inspect/SKILL.md` lines 34-49 now show `type list` then `state list`/`state get` and state that `--type` takes the full package-qualified name. The `Unknown state type for state reference` error string is not indexed there. The UX lesson (explain unfamiliar state) is not a skill matter.
