---
# ── Existing fields (keep) ─────────────────────────────────────────
title: Scheduling from Inside a Workflow       # link text in every generated index
impact: HIGH                                   # CRITICAL | HIGH | MEDIUM | LOW-MEDIUM | LOW
impactDescription: One line — what goes wrong if the agent skips this file
tags: scheduling, workflow, spawn              # free-text search terms
# ── Navigation fields (new) ────────────────────────────────────────
step: servicer        # the ONE build step that reads this file:
                      #   shell | api | servicer | auth | frontend | tests | run | deploy | any
                      # A file two steps need should be split. `any` is for patterns-*
                      # and lookups (errors, versions) read at no fixed step.
applies: [mcp-ui, web-app, backend-only]   # front doors whose builds read it
always: false         # true = read before any code, every build (keep this list tiny)
verified: 1.6.0       # Reboot version this file was last checked against
docs: ""              # matching docs.reboot.dev URL, if any. When this file deliberately
                      # tightens a rule from the public docs, say how in one sentence
                      # under "When you are here".
---

<!--
Reference template. Every file under skills/*/references/ uses these
seven sections, in this order, with these exact headings. The concept
(lifecycle, api, servicer, …) comes from the filename prefix listed in
python/references/_sections.md, not from frontmatter.

Write a section with nothing to say as "None known." (or "Not
measured." under Scales as). Never omit it: an empty section is a
claim that there is nothing to know, an omitted one is an oversight.

Budget: aim for under 1,500 words. Everything an agent reads is re-sent
on every later turn. A fact goes in exactly one file; elsewhere, link.

`patterns-*` files may show more than one shape under "Do this" (they
compare alternatives on purpose) and use `step: any`. Every other
section rule still applies.
-->

# Scheduling from Inside a Workflow

## When you are here

One short paragraph naming the situation the agent is in when this is
the right file: "You are inside a `WorkflowContext` and need another
actor to do something later." Add one line on what this file does
*not* cover and where that lives.

## Do this

The canonical shape: one complete, minimal, copy-able example with
the imports it needs, and the two or three sentences that explain it.
No alternatives. A multi-step procedure (a decision table, a
classification tree) is fine here when the procedure *is* the shape.
Sub-headings (`###`) are allowed inside this section only.

## Never

Things that type-check or look right and are wrong. One bullet each,
the wrong form first, then the one-line reason and the right form.

- `self.ref().schedule(when=…)` from a workflow — a workflow has no
  `self`; use `context.spawn(...)` / `Type.ref(id).spawn(...)`.

## Limits

Hard bounds: sizes, counts, timeouts, ordering constraints, what is
not durable, what is not atomic, what the API does not do. A number
wherever one is known, and where it came from.

- None known.

## Scales as

Soft costs that should shape a design: relative cost of operations,
fan-out, how cost grows with participants or data size. A ratio or a
number where one is known, with its source ("measured in a load test
at 1.4.1", "framework design").

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `StateNotConstructed` | A reader ran against an actor that was never constructed | Construct it first, or catch `<Method>Aborted` |

The left column is the literal string the agent will be holding — copy
it from a real traceback. These rows feed the generated error index.
"None known." if none.

## See also

At most three links, each with a five-word reason.

- [`servicer-workflow-calls.md`](servicer-workflow-calls.md) — classify every awaited call
