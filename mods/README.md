# Mods

Claude Code mods that ship with the Reboot plugin: plugins of function
hooks that draw in Claude Code's interface and act on tool calls. Each
is its own plugin, listed in `.claude-plugin/marketplace.json` as a
dependency of `reboot`, so installing `reboot` in Claude Code installs
them too.

**Claude Code only.** Codex reads the shared `hooks/hooks.json` and
rejects its `modules` key, so a mod never goes there, and Codex's
catalog (`.agents/plugins/marketplace.json`) doesn't list the mods.
Anything a mod enforces is also written into the skills, which Codex
reads.

| Mod | What it does |
| --- | --- |
| [`reboot-progress`](reboot-progress/) | The band above the prompt: a Status heading, a sentence on what is being worked on now (the state types, methods and files involved), and buttons that open the dashboard and the app (their addresses shown on hover). App health (backend, frontend, tunnel) in the status line, and a toast when the app or the dashboard starts or stops. |
| [`reboot-schema-guard`](reboot-schema-guard/) | Refuses API edits an app with persisted dev state couldn't boot over (a deleted method, a reworded method description, a changed field tag or type, …), and holds other API edits until the model has read `api-schema-evolution.md` once per session. |

## How a mod works

A mod is a folder with a manifest, a hooks file and one hooks module:

```
<mod>/
├── .claude-plugin/plugin.json   # name, version, description, "types"
├── hooks/
│   ├── hooks.json               # { "modules": ["./register.tsx"] }
│   ├── register.tsx             # export const register: Register = on => { ... }
│   ├── <logic>.ts               # pure functions, no $: unit-tested
│   └── *.test.ts                # claude plugin test
└── types/index.d.ts             # the state the mod keeps (PluginState)
```

- **Hooks.** `on(event, matcher?, hook)` adds a hook; every hook is
  `($, e, next)`. `e` is the event's input; `next(e)` runs the other
  plugins and then Claude Code's own behavior. A hook watches (`await
  next(e)` and reads the result), rewrites (`next({ ...e, … })`) or
  answers by itself (the schema guard returns `{ deny }`).
- **`$`** is the mod's only way out (no Node, no DOM): `$.fs`,
  `$.process`, `$.model`, `$.ui`, `$.store`, …, each spelled noun then
  method.
- **Drawing.** A `ui.render` hook on a component (`AbovePrompt` for the
  band) returns a tree of `Box`, `Text`, `Button`, … from the surface's
  own element table (`$.ui.resolve(e)`): terminal, desktop, vscode or
  mobile. Each surface lays the tree out its own way.
- **State.** `$.state` (`atom`, `read`, `update`) holds a session's
  values and redraws what reads them; `$.store` keeps values across
  sessions (`reboot-progress` keeps each project's task there). The
  module's own variables start over on every reload.
- **Fail open.** Every hook on a gating event (`tool.call`,
  `prompt.submit`) ends in `.catch(($, e, next) => next(e))`, so a bug in
  a mod never blocks the person's work.

The API is early access and may change between releases; the
declarations Claude Code writes beside a loaded mod
(`.claude-plugin/types/`, gitignored) are the authority.

## Running them while you work on them

Load the mods from this checkout, so an edit here is what runs. In
`~/.claude/settings.json` (user settings; a project's settings can't
set it):

```json
"env": {
  "CLAUDE_CODE_PLUGIN_DIRS": "/path/to/reboot-plugin/mods/reboot-progress:/path/to/reboot-plugin/mods/reboot-schema-guard"
}
```

or for one session, `claude --plugin-dir mods/reboot-progress`. A
terminal session watches the folder and reloads on save; the Claude
desktop app loads a mod when a session starts, so see a change there
in a new session. Don't also install the mods from the marketplace on
the same machine, or both copies load.

## Checks before a commit

From the mod's folder:

```sh
claude plugin validate .     # manifest, module and what it calls, as the engine reads them
claude plugin test .         # the *.test.ts files, against the engine itself
tsc -p .                     # once the mod has loaded (it writes the tsconfig and types)
```

- **Logic** that needs no `$` lives in plain modules (`progress.ts`,
  `activity.ts`, `schema.ts`) with unit tests.
- **Drawing** is tested by mounting the component on both the terminal
  and desktop surfaces (`$.ui.mount`), pressing buttons by key.
- **Behavior that involves a model** (the activity summaries, the task
  classification) is checked by running real prompts through it: a
  headless `claude -p --plugin-dir <mod>` session with `--debug-file`,
  or the prompt function's output through `claude -p --model sonnet`.
- **Layout isn't covered.** The tests check what a tree holds, not how
  a surface lays it out, so look at a layout change in the Claude app
  before calling it done.

## Shipping

A new mod is a folder here plus an entry in
`.claude-plugin/marketplace.json` (its `source` the folder) and its name
in `reboot`'s `dependencies`. Never add its `modules` to the root
`hooks/hooks.json` (Codex reads that file).
