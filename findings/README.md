# Findings corpus

Ground truth about where agents stall when building on Reboot with
these skills. One file per item, imported from the findings files
kept in individual app projects. A restructure of the skills is done
when every item with `target: plugin` is either `Resolved` (with a
`resolved_by` pointing at a section that exists) or `Obsolete`.

## Layout

```
findings/
├── README.md            this file
├── sources.md           which source file each project's items came from
└── <project>/
    └── <NN>-<slug>.md   one item; NN is the item's order in its source
```

## Item format

```markdown
---
id: reboot-air-09
project: reboot-air
source: "reboot-air/REBOOT_FINDINGS.md §9"
reboot_version: 1.4.1
severity: red            # red | yellow | green | unrated
target: plugin           # plugin | framework | cloud | bdd | primer | positive
names:                   # skills / references the item names or implicates
  - python/references/rpc-refs.md
tags: [negative-space]   # see vocabulary below
cluster: "4.1"           # proposal change or task this lands in (4.1–4.6, A–G, 8.4)
duplicate_of: ""         # id of the canonical item for the same gap; omit when canonical. A duplicate carries its canonical's status
still_applies: unknown   # yes | no | unknown, as judged at import against the skills at 1.6.0 (a snapshot; `status` is current)
status: Open             # Open | Resolved | Obsolete
resolved_by: ""          # "<path> § <section>" once Resolved; see below
mechanism: ""            # optional: row | template | check | hook | shim | tool | prose | eval
---

# <one-line title>

**What happened.** …

**Expected.** …

**Repro.** …

**Where in the skills.** …
```

Sections with nothing to say in the source are written `Not recorded.`
rather than invented.

### `target`

- `plugin` — the skills, references, hooks or shims in this repo
- `framework` — Reboot runtime or `rbt` behaviour (file upstream)
- `cloud` — Reboot Cloud
- `bdd` — `reboot.bdd`
- `primer` — belongs in the Reboot primer/book, not the plugin
- `positive` — something that worked and should be kept

An item can be about framework behaviour *and* be a plugin gap because
no skill mentions it. Use `plugin` whenever the fix includes writing
something down in a skill.

### `tags`

`negative-space` (a limit / non-behaviour nobody documents),
`contradiction` (two sections disagree; the item must name both),
`error-text` (an error string that should be in the error index),
`version-drift` (a reference names a symbol/flag the pinned Reboot
rejects), `scaffold` (a pasted template file is wrong), `seeding`,
`cost` (performance / scale), `pattern` (a reusable design pattern),
`operations` (run / stop / restart / dashboard / inspect),
`index-gap` (fact exists but no reading list points at it),
`builder-drift` (mcp-ui / web-app copies disagree), `auth`, `testing`,
`frontend`.

### `resolved_by` and `mechanism`

`resolved_by` lists what closed the item, separated by `; `. Each entry
must name something that exists (`tools/findings.py --check`):

- A path under `skills/` with `§ <heading>`: prose. The heading must
  exist outside code fences. The `§` part is required.
- A path under `skills/build/templates/`: a template file. `§` is
  optional.
- A repo path whose first segment is `hooks`, `hooks-handlers`, `bin`,
  `lib`, `tools` or `evals`: a check, hook, shim, tool or eval. `§` is
  optional. With it, `§` names a heading in a `.md` file, a `def` or
  `class` in a `.py` file, a function in a shell script, or a grader
  of an eval case (`evals/<case> § <grader>`, for
  `evals/<case>/graders/<grader>.md`).

`mechanism` is optional and says which kind of fix closed the item:
`row` (an Errors table row), `template`, `check`, `hook`, `shim`,
`tool`, `prose` or `eval`. Set it when an item is resolved; existing
items are not flipped in bulk.
