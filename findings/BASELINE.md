# Phase 0 baseline

Measured on 2026-10-04 against plugin `1f4f7bf` (Reboot 1.6.0), before
any restructuring. Every number here is reproducible with the tools in
`tools/`; rerun them to see how a change moved it.

## Reading cost (`tools/budget.py`)

What an agent reads before writing application code, if it follows the
skills exactly: the five SKILL.md files every build reads (`app`, the
builder, `python`, `feature`, `run`) plus every reference in the
builder's "Which References to Read, and When" list. "Minimal" drops
references whose sentence makes them conditional ("only when you
declared a `Workflow`", "for custom steps", …).

| Front door | SKILL.md | References | Words, all listed | Words, minimal | ≈ Tokens, minimal |
| --- | ---: | ---: | ---: | ---: | ---: |
| mcp-ui | 13,087 | 43 | 65,444 | **48,306** | ~64,400 |
| web-app | 11,861 | 34 | 52,456 | **37,127** | ~49,500 |

Largest single files on the path: `servicer-workflow.md` 8,106 (conditional),
`mcp-ui/SKILL.md` 5,490, `web-app/SKILL.md` 4,264, `python/SKILL.md` 2,971,
`auth-oauth-providers.md` 2,931, `testing-features.md` 2,680.

Proposal target (§4.5): 30,000 words on each minimal path.

## CLI drift (`tools/check-cli.py`)

**0 problems.** Every `rbt` invocation and `.rbtrc` line in the skills
(about 270 mentions) uses subcommands and flags that `rbt` 1.6.0 accepts.
The earlier drift the findings report (`dashboard --api-directory`,
`application_port`) has already been fixed upstream.

## Symbol drift (`tools/check-symbols.py`)

**99 distinct `reboot…` symbols from 295 mentions; 8 unresolved, which
are 3 defects:**

| Finding | Symbol(s) | Where |
| --- | --- | --- |
| `tool-checks-01` 🔴 | `reboot.std.oauth.v1.oauth` (`oauth_library`, `GOOGLE`, `GITHUB`, `_key_manager_id`) is not in the 1.6.0 wheel at all | `stdlib-oauth-tokens.md`, `auth-external-api-calls.md`, `mcp-ui/…/auth-store-tokens.md` |
| `tool-checks-02` 🟡 | `Subscriber` / `MousePosition` labelled with module paths that don't exist; they live in `reboot.std.presence.v1.presence` | `stdlib-presence.md` |
| `tool-checks-03` 🟢 | React hooks given a Python module path `reboot.std.react.presence` | `stdlib-presence.md` |

`tool-checks-01` is likely a framework packaging bug (the framework's own
boot error names the same missing module). Confirm on a Linux wheel
before filing upstream.

## Findings corpus (`tools/findings.py`)

363 items from 16 findings files plus the tool checks above
(Reboot 1.4.0 → 1.6.0).

| Target | Items |
| --- | ---: |
| plugin | 225 |
| positive (keep) | 59 |
| framework | 49 |
| primer | 19 |
| bdd | 9 |
| cloud | 2 |

Plugin items: **213 open**, 11 obsolete (fixed upstream by 1.6.0),
1 already resolved.

Open plugin items by where the proposal says they land:

| Cluster | Open | Meaning |
| --- | ---: | --- |
| 4.1 | 82 | a Never / Limits / Errors line in an existing reference |
| D | 32 | cost, scale, performance ("Scales as", benchmarking reference) |
| F | 21 | run / stop / restart, dashboard, inspect |
| E | 20 | positive design patterns (`patterns-*`) |
| 4.2 | 14 | the shared build spine, mcp-ui vs web-app drift, `run` detection |
| C | 12 | seeding and `initialize` |
| 8.4 | 12 | smaller items (type-checking, dev loop, docs divergence, …) |
| B | 7 | scaffold files as real templates |
| 4.4 | 7 | error-index rows only |
| A | 4 | version drift (including the three tool checks) |
| G | 2 | hook reminder / design-phase lines |

Most-named in open plugin items: `run/SKILL.md` 27, `web-app/SKILL.md` 23,
`servicer-workflow.md` 22, `servicer-transaction.md` 17,
`react-generated-client.md` 16, `testing-harness.md` 16,
`web-app/references/react-client.md` 15, `lifecycle-initialize-hook.md` 13.

Tags across all items: negative-space 158, pattern 109, error-text 100,
testing 72, operations 66, cost 60, contradiction 50.

### Known corpus caveats

- Several items describe the same gap from different projects (e.g. the
  `allowed_origins` items, the transaction-size limit, "how to stop the
  app"). They are not yet linked; a `duplicate_of` field is the next step.
- `target` and `cluster` were assigned by four readers working in parallel
  against the same README; borderline calls (framework vs plugin, primer
  vs plugin) are noted in the import reports and worth a human pass.
- 34 plugin items have `still_applies: unknown`.
