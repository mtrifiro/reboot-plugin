// The schema guard: stops API edits a Reboot app with persisted state
// couldn't boot over. One command hook for Claude Code and Codex
// (`hooks/schema-guard.sh` starts it; `hooks/hooks.json` registers it):
//
//   - PreToolUse on an edit (Claude Code's Edit, MultiEdit and Write;
//     Codex's apply_patch): in a project with persisted state (dev state
//     under `.rbt/dev/`, or a production deploy in
//     `deploy/ledger.jsonl`), builds each changed API definition file in
//     memory and refuses the edit when the runtime couldn't boot over the
//     change; an edit that is fine still waits until the session has
//     read all of `api-schema-evolution.md`.
//   - PreToolUse on Bash: refuses a shell command that rewrites an API
//     file (`sed -i`, a redirect, `mv`, `git checkout`, ...), which the
//     check above can't see.
//   - PostToolUse on Read and Bash: records which lines of the rules
//     file were shown (a Read, `cat`, `sed -n 'a,bp'`, `head`, `tail`),
//     so the rules count as read once every line has been, over one
//     call or several.
//   - PostCompact: the rules are out of the model's context again.
//
// The comparison itself is `schema.ts` beside this file. Every failure
// is silent: a guard that breaks must not stop the build.

import { existsSync, mkdirSync, readFileSync, readdirSync, realpathSync, renameSync, rmSync, writeFileSync } from 'node:fs'
import { homedir, tmpdir } from 'node:os'
import { dirname, isAbsolute, join, resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

import { applicationName, bashEditsApi, incompatibilities, isApiFile, isApiPath } from './schema.ts'

const NAME = 'reboot schema guard'
const RULES = 'api-schema-evolution.md'
const PLUGIN = (process.env.PLUGIN_ROOT || process.env.CLAUDE_PLUGIN_ROOT || '').replace(/\/+$/, '')
const RULES_FILE = PLUGIN ? `${PLUGIN}/skills/python/references/${RULES}` : null
const RULES_PATH = RULES_FILE ?? `the reboot plugin's skills/python/references/${RULES}`

// ---------------------------------------------------------------- project

/** The nearest ancestor of `path` holding a `.rbtrc`, up to six levels. */
export function projectOf(path) {
  let dir = dirname(path)
  for (let i = 0; i < 6 && dir !== '/'; i++) {
    if (existsSync(join(dir, '.rbtrc'))) return dir
    dir = dirname(dir)
  }

  return null
}

/** Where the project holds state the API must boot over, else null. */
export function stateOf(root) {
  const dev = join(root, '.rbt/dev')
  if (existsSync(dev)) {
    const name = applicationName(readOr(join(root, '.rbtrc')) ?? '')
    const has = name
      ? existsSync(join(dev, name))
      : readdirSync(dev, { withFileTypes: true }).some(entry => entry.isDirectory())
    if (has) return dev
  }
  if (existsSync(join(root, 'deploy/ledger.jsonl'))) return `${root}/deploy/ledger.jsonl, a production deploy`

  return null
}

function readOr(path) {
  try {
    return readFileSync(path, 'utf8')
  } catch {
    return null
  }
}

// ------------------------------------------------------------ apply_patch

/**
 * The file operations of an `apply_patch` input, or null when it isn't
 * one this can read. The input is the patch itself or a command holding
 * it (`apply_patch <<'EOF' ... EOF`).
 */
export function parsePatch(input) {
  const begin = input.indexOf('*** Begin Patch')
  const end = input.lastIndexOf('*** End Patch')
  if (begin < 0 || end < begin) return null
  const lines = input.slice(begin, end).split('\n').slice(1)
  const ops = []
  let op = null
  let chunk = null
  const startChunk = context => {
    chunk = { context, old: [], new: [], eof: false }
    op.chunks.push(chunk)
  }
  for (const raw of lines) {
    const line = raw.replace(/\r$/, '')
    let m
    if ((m = line.match(/^\*\*\* (Add|Update|Delete) File: (.+)$/))) {
      op = { kind: m[1].toLowerCase(), path: m[2].trim(), moveTo: null, chunks: [], added: [] }
      chunk = null
      ops.push(op)
    } else if (!op) {
      if (line.trim() !== '') return null
    } else if ((m = line.match(/^\*\*\* Move to: (.+)$/))) {
      op.moveTo = m[1].trim()
    } else if (line === '*** End of File') {
      if (chunk) chunk.eof = true
    } else if (op.kind === 'add') {
      if (!line.startsWith('+')) return null
      op.added.push(line.slice(1))
    } else if (op.kind === 'update') {
      if (line.startsWith('@@')) startChunk(line.slice(2).trim() || null)
      else {
        if (!chunk) startChunk(null)
        if (line.startsWith('+')) chunk.new.push(line.slice(1))
        else if (line.startsWith('-')) chunk.old.push(line.slice(1))
        else if (line.startsWith(' ') || line === '') {
          chunk.old.push(line.slice(1))
          chunk.new.push(line.slice(1))
        } else return null
      }
    } else if (line.trim() !== '') return null
  }

  return ops
}

const NORMALIZERS = [s => s, s => s.trimEnd(), s => s.trim()]

/** Where `pattern` starts in `lines` at or after `start`, as apply_patch finds it. */
function seek(lines, pattern, start, eof) {
  if (pattern.length === 0) return start
  if (pattern.length > lines.length) return -1
  const last = lines.length - pattern.length
  const from = eof ? last : start
  for (const norm of NORMALIZERS) {
    for (let i = from; i <= last; i++) {
      if (pattern.every((p, j) => norm(lines[i + j]) === norm(p))) return i
    }
  }

  return eof ? seek(lines, pattern, start, false) : -1
}

/** `before` with an Update's chunks applied, or null when they don't apply. */
export function applyChunks(before, chunks) {
  const lines = before.split('\n')
  if (lines[lines.length - 1] === '') lines.pop()
  const replacements = []
  let cursor = 0
  for (const c of chunks) {
    if (c.context !== null) {
      const at = seek(lines, [c.context], cursor, false)
      if (at < 0) return null
      cursor = at + 1
    }
    if (c.old.length === 0) {
      replacements.push([lines.length, 0, c.new])
      continue
    }
    let old = c.old
    let neu = c.new
    let at = seek(lines, old, cursor, c.eof)
    if (at < 0 && old[old.length - 1] === '') {
      old = old.slice(0, -1)
      neu = neu[neu.length - 1] === '' ? neu.slice(0, -1) : neu
      at = seek(lines, old, cursor, c.eof)
    }
    if (at < 0) return null
    replacements.push([at, old.length, neu])
    cursor = at + old.length
  }
  replacements.sort((a, b) => b[0] - a[0])
  for (const [at, count, neu] of replacements) lines.splice(at, count, ...neu)

  return `${lines.join('\n')}\n`
}

/**
 * The changes an `apply_patch` input makes, each as a path, where it
 * moves to, and a function from the file's text to its new text (null
 * when the patch doesn't apply, which apply_patch refuses itself).
 */
export function patchChanges(input, cwd) {
  return (parsePatch(input) ?? []).map(op => ({
    path: resolve(cwd, op.path),
    dest: op.moveTo ? resolve(cwd, op.moveTo) : null,
    apply: before =>
      op.kind === 'delete'
        ? ''
        : op.kind === 'add'
          ? op.added.length ? `${op.added.join('\n')}\n` : ''
          : applyChunks(before, op.chunks),
  }))
}

/** `text` with one Claude Code Edit applied, as the tool applies it. */
const replaceIn = (text, { old_string: from, new_string: to, replace_all: all }) =>
  typeof from !== 'string' || typeof to !== 'string' || from === ''
    ? text
    : all
      ? text.split(from).join(to)
      : text.replace(from, () => to)

/** The change a Claude Code Edit, MultiEdit or Write makes, as `patchChanges` gives one. */
export function editChanges(tool, input, cwd) {
  if (typeof input?.file_path !== 'string') return []
  const path = resolve(cwd, input.file_path)
  if (tool === 'Write') return [{ path, dest: null, apply: () => (typeof input.content === 'string' ? input.content : null) }]
  if (tool === 'Edit') return [{ path, dest: null, apply: before => replaceIn(before, input) }]
  if (tool === 'MultiEdit' && Array.isArray(input.edits)) {
    return [{ path, dest: null, apply: before => input.edits.reduce(replaceIn, before) }]
  }

  return []
}

/**
 * For each change to an existing API file in a project with state, what
 * the runtime would refuse. `guarded` says whether any change was to
 * one (a new API file is additive, so it isn't).
 */
export function check(changes) {
  const problems = []
  const states = new Set()
  let guarded = false
  for (const { path, dest, apply } of changes) {
    if (!isApiPath(path) && !(dest && isApiPath(dest))) continue
    const target = isApiPath(path) ? path : dest
    const root = projectOf(target)
    if (!root || !isApiFile(target, root)) continue
    const state = stateOf(root)
    if (state === null) continue
    const before = readOr(path)
    if (before === null) continue
    const after = apply(before)
    if (after === null) continue
    guarded = true
    states.add(state)
    const rel = path.slice(root.length + 1)
    if (dest && dest !== path) {
      problems.push(`\`${rel}\` is moved to \`${dest.slice(root.length + 1)}\`, which the guard can't check; edit it in place`)
    }
    for (const p of incompatibilities(before, after)) problems.push(`${rel}: ${p}`)
  }

  return { problems, states: [...states], guarded }
}

// ------------------------------------------------------- reading the rules

function rulesPathIn(command, cwd) {
  const m = command.match(/(["']?)([^\s"'|;&<>]*api-schema-evolution\.md)\1/)
  if (!m) return null
  let path = m[2]
  if (path.startsWith('~/')) path = join(homedir(), path.slice(2))
  else if (path.startsWith('$HOME/')) path = join(homedir(), path.slice(6))
  else if (/^\$\{?(CLAUDE_)?PLUGIN_ROOT\}?\//.test(path) && PLUGIN) path = PLUGIN + path.slice(path.indexOf('/'))

  return isAbsolute(path) ? path : resolve(cwd, path)
}

/**
 * The line ranges of the rules file a shell command prints, 1-based and
 * inclusive, or null when it prints none of it (a grep, a word count).
 */
export function linesShown(command, total) {
  if (!command.includes(RULES)) return null
  const ranges = []
  if (/\bsed\b[^|;&]*\s-n\b/.test(command)) {
    for (const m of command.matchAll(/(\d+)\s*(?:,\s*(\d+|\$))?\s*p\b/g)) {
      const a = Number(m[1])
      const b = m[2] === undefined ? a : m[2] === '$' ? total : Number(m[2])
      ranges.push([a, b])
    }
    return ranges.length ? ranges : null
  }
  let m
  if ((m = command.match(/\bhead\b(?:\s+-n)?\s+-?(\d+)\b/))) return [[1, Number(m[1])]]
  if (/\bhead\b/.test(command)) return [[1, 10]]
  if ((m = command.match(/\btail\b(?:\s+-n)?\s+\+(\d+)\b/))) return [[Number(m[1]), total]]
  if ((m = command.match(/\btail\b(?:\s+-n)?\s+-?(\d+)\b/))) return [[total - Number(m[1]) + 1, total]]
  if (/\btail\b/.test(command)) return [[total - 9, total]]
  if (/\b(cat|nl|bat|less|more)\b/.test(command)) return [[1, total]]

  return null
}

/** Ranges merged, overlapping and adjacent ones joined. */
export function merge(ranges) {
  const sorted = ranges.map(([a, b]) => [Math.max(1, a), b]).filter(([a, b]) => a <= b).sort((x, y) => x[0] - y[0])
  const out = []
  for (const [a, b] of sorted) {
    const last = out[out.length - 1]
    if (last && a <= last[1] + 1) last[1] = Math.max(last[1], b)
    else out.push([a, b])
  }

  return out
}

function stateFile(session) {
  const base = process.env.PLUGIN_DATA || process.env.CLAUDE_PLUGIN_DATA || join(tmpdir(), 'reboot-plugin')
  const safe = String(session || 'unknown').replace(/[^\w.-]/g, '_')

  return join(base, 'schema-guard', `${safe}.json`)
}

function loadSession(session) {
  try {
    return JSON.parse(readFileSync(stateFile(session), 'utf8'))
  } catch {
    return { read: false, shown: [] }
  }
}

function saveSession(session, value) {
  const file = stateFile(session)
  mkdirSync(dirname(file), { recursive: true })
  const tmp = `${file}.${process.pid}`
  writeFileSync(tmp, JSON.stringify(value))
  renameSync(tmp, file)
}

function failed(response) {
  if (!response || typeof response !== 'object') return false
  const code = response.exit_code ?? response.exitCode ?? response.metadata?.exit_code

  return typeof code === 'number' && code !== 0
}

// ------------------------------------------------------------------ events

const deny = reason => ({
  hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason: reason },
})

const EDITS = new Set(['Edit', 'MultiEdit', 'Write'])

/** Records lines of the rules file a call showed; marks them read once all have been. */
function recordShown(session, text, shown) {
  if (!shown) return
  const total = text.split('\n').length - (text.endsWith('\n') ? 1 : 0)
  const state = loadSession(session)
  const merged = merge([...state.shown, ...shown.map(([a, b]) => [a, Math.min(b, total)])])
  const read = merged.length === 1 && merged[0][0] <= 1 && merged[0][1] >= total
  saveSession(session, { read: state.read || read, shown: merged })
}

/**
 * The hook's answer to one event, or null to let the call through.
 * Codex sends a `turn_id` with these events and Claude Code doesn't;
 * only the wording of a refusal depends on which agent it is.
 */
export function handle(e) {
  if (!e || typeof e !== 'object') return null
  const codex = Boolean(e.turn_id)
  const cwd = e.cwd || process.cwd()
  const input = e.tool_input && typeof e.tool_input === 'object' ? e.tool_input : {}
  const command = typeof input.command === 'string' ? input.command : ''
  const editTools = codex ? 'apply_patch' : 'the Edit or Write tool'

  if (e.hook_event_name === 'PostCompact') {
    rmSync(stateFile(e.session_id), { force: true })
    return null
  }

  if (e.hook_event_name === 'PostToolUse') {
    if (e.tool_name === 'Read' && typeof input.file_path === 'string' && input.file_path.endsWith(`/${RULES}`)) {
      const text = readOr(resolve(cwd, input.file_path))
      if (!text) return null
      // Read's offset is the 1-based first line; without a limit it reads 2000 lines.
      const from = Math.max(1, Number(input.offset) || 1)
      const count = Number(input.limit) > 0 ? Number(input.limit) : 2000
      recordShown(e.session_id, text, [[from, from + count - 1]])
    } else if (e.tool_name === 'Bash' && command.includes(RULES) && !failed(e.tool_response)) {
      const path = rulesPathIn(command, cwd)
      const text = (path && readOr(path)) ?? (RULES_FILE && readOr(RULES_FILE))
      if (!text) return null
      const total = text.split('\n').length - (text.endsWith('\n') ? 1 : 0)
      recordShown(e.session_id, text, linesShown(command, total))
    }
    return null
  }

  if (e.hook_event_name !== 'PreToolUse') return null

  const changes =
    e.tool_name === 'apply_patch' ? patchChanges(command, cwd) : EDITS.has(e.tool_name) ? editChanges(e.tool_name, input, cwd) : null
  if (changes) {
    const { problems, states, guarded } = check(changes)
    if (!guarded) return null
    const state = states.join('; ')
    if (problems.length > 0) {
      return deny(
        `${NAME}: this app has persisted state (${state}), and the runtime refuses to boot ` +
          `over these API changes:\n- ${problems.join('\n- ')}\n` +
          `Make the change additively instead (a new method or field, the old one kept), per ` +
          `${RULES_PATH}. Expunging dev state would also allow it, but deletes the app's data: ` +
          `ask the user before running \`rbt dev expunge\`.`,
      )
    }
    if (!loadSession(e.session_id).read) {
      return deny(
        `${NAME}: this app has persisted state (${state}), so only additive API changes boot. ` +
          `Read all of ${RULES_PATH} and check this change against its table, then make the ` +
          `edit again.`,
      )
    }
    return null
  }

  if (e.tool_name === 'Bash' && bashEditsApi(command)) {
    const root = projectOf(`${cwd}/.`)
    const state = root && stateOf(root)
    if (!state) return null
    return deny(
      `${NAME}: this app has persisted state (${state}), and this command rewrites an API ` +
        `definition file where the guard can't check it. Make the change with ${editTools} ` +
        `instead, additively per ${RULES_PATH}.`,
    )
  }

  return null
}

async function main() {
  let input = ''
  for await (const chunk of process.stdin) input += chunk
  const answer = handle(JSON.parse(input))
  if (answer) process.stdout.write(`${JSON.stringify(answer)}\n`)
}

if (process.argv[1] && import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href) {
  main().catch(() => process.exit(0))
}
