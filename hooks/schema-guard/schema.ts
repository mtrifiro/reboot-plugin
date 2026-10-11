// Pure logic for the schema guard (`guard.mjs`): what an API file
// declares, and which changes between two versions of it the runtime
// refuses over persisted state. Follows the table in
// skills/python/references/api-schema-evolution.md. Regex, not a
// parser: it reads the shape the build templates write.

export type Field = { name: string; type: string; hasDefault: boolean }
export type Method = { kind: string; description: string | null; isFactory: boolean }

export type Schema = {
  /** Model class → field tag → the field. */
  models: Map<string, Map<number, Field>>
  /** State Type → method name → the method. */
  types: Map<string, Map<string, Method>>
}

const STRING = String.raw`(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')`
const DESCRIPTION = new RegExp(String.raw`description\s*=\s*\(?((?:\s*${STRING})+)`)
const METHOD = /(\w+)\s*=\s*(Reader|Writer|Transaction|Workflow|UI)\s*\(/g
const TYPE = /(\w+)\s*=\s*Type\s*\(/g
const FIELD = /^\s+(\w+)\s*:\s*([^=\n]+?)\s*=\s*Field\(/gm

/** The text of adjacent string literals, quotes and joins removed. */
const literal = (s: string) =>
  [...s.matchAll(new RegExp(STRING, 'g'))].map(m => m[0].slice(1, -1)).join('')

/** The text inside the parentheses opened just before `from`, nesting kept. */
function balanced(text: string, from: number): string {
  let depth = 1
  for (let i = from; i < text.length; i++) {
    const c = text[i]
    if (c === '(' || c === '[' || c === '{') depth++
    else if (c === ')' || c === ']' || c === '}') {
      depth--
      if (depth === 0) return text.slice(from, i)
    }
  }

  return text.slice(from)
}

/**
 * A type's spelling, normalized: the runtime keys data by tag and shape,
 * not by how the annotation is written, so `Optional[str]` and
 * `str | None` are one type, as are `List[int]` and `list[int]`.
 */
export function normalizeType(type: string): string {
  let t = type.replace(/\s+/g, '')
  t = t.replace(/\b(typing\.)?(List|Dict|Set|Tuple|FrozenSet|Type)\[/g, (_, __, name: string) => `${name.toLowerCase()}[`)
  for (;;) {
    const m = t.match(/\b(typing\.)?Optional\[/)
    if (!m) break
    const start = m.index! + m[0].length
    const inner = balanced(t, start)
    t = `${t.slice(0, m.index!)}${inner}|None${t.slice(start + inner.length + 1)}`
  }
  // A union's order doesn't matter: `None|str` is `str|None`.
  if (t.includes('|') && !/[[\]]/.test(t)) t = t.split('|').sort().join('|')

  return t
}

export function parse(text: string): Schema {
  const models: Schema['models'] = new Map()
  for (const block of text.split(/^(?=class\s)/m)) {
    const cls = block.match(/^class\s+(\w+)\s*\(/)
    if (!cls) continue
    const fields = new Map<number, Field>()
    for (const f of block.matchAll(FIELD)) {
      const args = balanced(block, f.index! + f[0].length)
      const tag = args.match(/\btag\s*=\s*(\d+)/)
      if (tag) {
        fields.set(Number(tag[1]), {
          name: f[1]!,
          type: normalizeType(f[2]!),
          hasDefault: /\bdefault(_factory)?\s*=/.test(args),
        })
      }
    }
    models.set(cls[1]!, fields)
  }

  const types: Schema['types'] = new Map()
  const typeStarts = [...text.matchAll(TYPE)]
  typeStarts.forEach((t, i) => {
    const body = text.slice(t.index!, typeStarts[i + 1]?.index ?? text.length)
    const methods = new Map<string, Method>()
    const calls = [...body.matchAll(METHOD)]
    calls.forEach((m, j) => {
      const call = body.slice(m.index!, calls[j + 1]?.index ?? body.length)
      const d = call.match(DESCRIPTION)
      methods.set(m[1]!, {
        kind: m[2]!,
        description: d ? literal(d[1]!) : null,
        isFactory: /\bfactory\s*=\s*True\b/.test(call),
      })
    })
    types.set(t[1]!, methods)
  })

  return { models, types }
}

/** Method kinds that may change into each other, other options unchanged. */
const COMPATIBLE_KINDS = new Set(['Writer:Transaction', 'Transaction:Writer'])

/** Each change from `before` to `after` the runtime refuses, in words. */
export function incompatibilities(before: string, after: string): string[] {
  const a = parse(before)
  const b = parse(after)
  const problems: string[] = []

  for (const [type, methods] of a.types) {
    const next = b.types.get(type)
    if (!next) {
      problems.push(`state type \`${type}\` is deleted or renamed`)
      continue
    }
    for (const [name, m] of methods) {
      const n = next.get(name)
      if (!n) {
        problems.push(`method \`${type}.${name}\` is deleted or renamed`)
        continue
      }
      if (n.kind !== m.kind) {
        if (!COMPATIBLE_KINDS.has(`${m.kind}:${n.kind}`)) {
          problems.push(`method \`${type}.${name}\` changes kind, ${m.kind} → ${n.kind}`)
        } else if (m.isFactory || n.isFactory) {
          problems.push(`method \`${type}.${name}\` changes kind on a \`factory=True\` constructor, ${m.kind} → ${n.kind}`)
        }
      }
      // Reboot intends to push an upstream fix that lets a method's
      // description change after it is created; drop this check for the
      // Reboot release that ships it.
      if (n.description !== m.description) {
        problems.push(
          m.description === null
            ? `method \`${type}.${name}\` gains a \`description=\` (it is part of the method's options)`
            : `method \`${type}.${name}\`'s \`description=\` changes`,
        )
      }
    }
  }

  // A renamed model class is compatible; pair one gone with one new.
  const gone = [...a.models.keys()].filter(c => !b.models.has(c))
  const added = [...b.models.keys()].filter(c => !a.models.has(c))
  const renamed = gone.length === 1 && added.length === 1 ? new Map([[gone[0]!, added[0]!]]) : null

  for (const [cls, fields] of a.models) {
    const after = renamed?.get(cls) ?? cls
    const next = b.models.get(after)
    if (!next) continue // the class itself is gone; its Type's methods say whether that matters
    for (const [tag, f] of fields) {
      const n = next.get(tag)
      if (!n) problems.push(`field \`${cls}.${f.name}\` (tag ${tag}) is deleted or its tag changed`)
      else {
        if (n.type !== f.type) {
          problems.push(`field \`${cls}.${f.name}\` (tag ${tag}) changes type, ${f.type} → ${n.type}`)
        }
        if (f.hasDefault && !n.hasDefault) {
          problems.push(`field \`${cls}.${f.name}\` (tag ${tag}) loses its default (required-ness can't change)`)
        }
      }
    }
    for (const [tag, n] of next) {
      if (!fields.has(tag) && !n.hasDefault) {
        problems.push(`field \`${after}.${n.name}\` (tag ${tag}) is added without a default`)
      }
    }
  }

  return problems
}

/** A path shaped like an API definition file: `api/<pkg>/v1/<name>.py`, not generated. */
export const isApiPath = (path: string): boolean =>
  /\/api\/[^/]+\/v1\/[^/]+\.py$/.test(path) && !/_rbt\.py$/.test(path)

/**
 * An API definition file the build writes, not generated code: the
 * project's own `api/`, not one under its `backend/`, `frontend/` or
 * `web/`. The exclusion is tested on the path relative to the project
 * root when the root is known, so a project that itself lives under a
 * directory named `web` is still guarded.
 */
export const isApiFile = (path: string, root: string | null = null): boolean => {
  if (!isApiPath(path)) return false
  const rel = root !== null && path.startsWith(`${root}/`) ? path.slice(root.length) : path

  return !/\/(backend|frontend|web)\/[^]*api\//.test(rel)
}

/**
 * Whether a shell command rewrites an API definition file, which the
 * guard can't check: an in-place sed or perl, a redirect into it, a
 * move, copy, link, tee or delete of it, or a git checkout, restore,
 * stash or reset that would replace it. Reading one (`cat`, `grep`,
 * `sed -n`) is not.
 *
 * The command is split into simple commands (on `&&`, `||`, `;`, `|`,
 * `&`, newlines and parentheses; a heredoc's body is skipped), and
 * `cd`, `pushd` and `popd` move the directory later paths resolve
 * against. With the project's `root` known, a write is refused when
 * its target is `<root>/api`, anything under it, or a directory that
 * holds it (the root or an ancestor, as in `rm -rf .`); a glob counts
 * when it could match one of those. Without the root, only a target
 * shaped like an API definition file counts. `exists` tells a path
 * from a branch in `git checkout <name>`.
 */
export function bashEditsApi(
  command: string,
  cwd: string = '/',
  root: string | null = null,
  exists: (path: string) => boolean = () => false,
): boolean {
  const home = process.env.HOME ?? '/'
  const apiDir = root === null ? null : normalize(`${root}/api`)
  const covers = (path: string): boolean => {
    if (apiDir === null) return /(^|\/)api\/[^/]+\/v1\/[^/]+\.py$/.test(path) && !/_rbt\.py$/.test(path)
    return sameLine(path, apiDir)
  }
  const at = (dir: string, word: string): string =>
    normalize(word.startsWith('~') ? home + word.slice(1) : word.startsWith('/') ? word : `${dir}/${word}`)

  let dir = normalize(cwd)
  const subshells: string[] = []
  const pushed: string[] = []
  for (const piece of simpleCommands(command)) {
    if (piece === '(') {
      subshells.push(dir)
      continue
    }
    if (piece === ')') {
      dir = subshells.pop() ?? dir
      continue
    }
    const { words, writes } = piece
    if (writes.some(w => covers(at(dir, w)))) return true
    const args = stripPrefixes(words)
    if (args.length === 0) continue
    const name = args[0]!.replace(/.*\//, '')
    const rest = args.slice(1)
    if (name === 'cd' || name === 'pushd') {
      const to = rest.find(a => !a.startsWith('-') || a === '-')
      if (name === 'pushd') pushed.push(dir)
      if (to === undefined) dir = normalize(home)
      else if (to !== '-') dir = at(dir, to)
      continue
    }
    if (name === 'popd') {
      dir = pushed.pop() ?? dir
      continue
    }
    if (name === 'git') {
      const target = gitTargets(rest, dir, at, exists)
      if (target === 'all') return true
      if (target.some(covers)) return true
      continue
    }
    if (writeTargets(name, rest).some(w => covers(at(dir, w)))) return true
  }

  return false
}

type Piece = { words: string[]; writes: string[] } | '(' | ')'

/** POSIX path normalization, keeping glob characters as they are. */
function normalize(path: string): string {
  const out: string[] = []
  for (const part of path.split('/')) {
    if (part === '' || part === '.') continue
    if (part === '..') out.pop()
    else out.push(part)
  }

  return `/${out.join('/')}`
}

const GLOB = /[*?[{]/

function globPart(part: string): RegExp {
  let re = ''
  let braces = 0
  for (let i = 0; i < part.length; i++) {
    const c = part[i]!
    if (c === '*') re += '[^/]*'
    else if (c === '?') re += '[^/]'
    else if (c === '[') {
      const end = part.indexOf(']', i + 1)
      if (end < 0) re += '\\['
      else {
        re += `[${part.slice(i + 1, end).replace(/^!/, '^').replace(/\\/g, '\\\\')}]`
        i = end
      }
    } else if (c === '{') {
      braces++
      re += '(?:'
    } else if (c === '}' && braces > 0) {
      braces--
      re += ')'
    } else if (c === ',' && braces > 0) re += '|'
    else re += c.replace(/[.+^$()|\\]/g, '\\$&')
  }

  return new RegExp(`^${re}$`)
}

/** Whether `path` (maybe a glob) is `target`, holds it, or lies under it. */
function sameLine(path: string, target: string): boolean {
  const a = path.split('/').filter(Boolean)
  const b = target.split('/').filter(Boolean)
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    const part = a[i]!
    if (GLOB.test(part) ? !globPart(part).test(b[i]!) : part !== b[i]) return false
  }

  return true
}

/**
 * The command split into simple commands, each with its words (quotes
 * removed) and the files its output redirections write; `(` and `)`
 * mark a subshell or command substitution.
 */
function simpleCommands(command: string): Piece[] {
  const pieces: Piece[] = []
  let words: string[] = []
  let writes: string[] = []
  let word: string | null = null
  let redirect: 'write' | 'read' | 'dup' | 'heredoc' | null = null
  const heredocs: { end: string; strip: boolean }[] = []
  let heredocStrip = false

  const endWord = () => {
    if (word === null) return
    if (redirect === 'write') writes.push(word)
    else if (redirect === 'dup') {
      if (!/^(\d+|-)$/.test(word)) writes.push(word)
    } else if (redirect === 'heredoc') heredocs.push({ end: word, strip: heredocStrip })
    else if (redirect === null) words.push(word)
    redirect = null
    word = null
  }
  const endCommand = () => {
    endWord()
    if (words.length > 0 || writes.length > 0) pieces.push({ words, writes })
    words = []
    writes = []
  }

  const s = command
  let i = 0
  while (i < s.length) {
    const c = s[i]!
    if (c === '\\' && i + 1 < s.length) {
      if (s[i + 1] === '\n') {
        i += 2
        continue
      }
      word = (word ?? '') + s[i + 1]
      i += 2
      continue
    }
    if (c === "'") {
      const end = s.indexOf("'", i + 1)
      const stop = end < 0 ? s.length : end
      word = (word ?? '') + s.slice(i + 1, stop)
      i = stop + 1
      continue
    }
    if (c === '"') {
      let j = i + 1
      let text = ''
      while (j < s.length && s[j] !== '"') {
        if (s[j] === '\\' && j + 1 < s.length && '"\\$`'.includes(s[j + 1]!)) {
          text += s[j + 1]
          j += 2
        } else text += s[j++]
      }
      word = (word ?? '') + text
      i = j + 1
      continue
    }
    if (c === ' ' || c === '\t') {
      endWord()
      i++
      continue
    }
    if (c === '#' && word === null) {
      while (i < s.length && s[i] !== '\n') i++
      continue
    }
    if (c === '\n') {
      endCommand()
      i++
      // Heredoc bodies are data, not commands.
      for (const { end, strip } of heredocs.splice(0)) {
        while (i < s.length) {
          const eol = s.indexOf('\n', i)
          const line = s.slice(i, eol < 0 ? s.length : eol)
          i = eol < 0 ? s.length : eol + 1
          if ((strip ? line.replace(/^\t+/, '') : line) === end) break
        }
      }
      continue
    }
    if (c === '$' && s[i + 1] === '(') {
      endCommand()
      pieces.push('(')
      i += 2
      continue
    }
    if (c === '(' || c === ')') {
      endCommand()
      pieces.push(c)
      i++
      continue
    }
    if (c === '`') {
      endCommand()
      i++
      continue
    }
    if (c === '&' && s[i + 1] === '>') {
      endWord()
      i += s[i + 2] === '>' ? 3 : 2
      redirect = 'write'
      continue
    }
    if (c === ';' || c === '|' || c === '&') {
      endCommand()
      i += s[i + 1] === c ? 2 : 1
      continue
    }
    if (c === '>' || c === '<') {
      // A word of digits right before is the descriptor, not a word.
      if (word !== null && /^\d+$/.test(word)) word = null
      endWord()
      if (c === '<') {
        if (s.startsWith('<<<', i)) {
          redirect = 'read'
          i += 3
        } else if (s.startsWith('<<', i)) {
          heredocStrip = s[i + 2] === '-'
          redirect = 'heredoc'
          i += heredocStrip ? 3 : 2
        } else if (s[i + 1] === '>') {
          redirect = 'write'
          i += 2
        } else {
          redirect = 'read'
          i += 1
        }
      } else if (s[i + 1] === '&') {
        redirect = 'dup'
        i += 2
      } else {
        redirect = 'write'
        i += s[i + 1] === '>' || s[i + 1] === '|' ? 2 : 1
      }
      continue
    }
    word = (word ?? '') + c
    i++
  }
  endCommand()

  return pieces
}

const PREFIXES = new Set(['sudo', 'command', 'builtin', 'exec', 'nohup', 'time', 'nice', 'env', 'xargs'])

/** The words after leading assignments and wrappers (`sudo`, `env`, ...). */
function stripPrefixes(words: string[]): string[] {
  let i = 0
  while (i < words.length) {
    const w = words[i]!
    if (/^[A-Za-z_][A-Za-z0-9_]*=/.test(w)) i++
    else if (PREFIXES.has(w.replace(/.*\//, ''))) {
      i++
      while (i < words.length && words[i]!.startsWith('-')) i++
    } else break
  }

  return words.slice(i)
}

/** Positional arguments, skipping options and the option arguments `takes` names. */
function positionals(args: string[], takes: Set<string> = new Set()): string[] {
  const out: string[] = []
  let options = true
  for (let i = 0; i < args.length; i++) {
    const a = args[i]!
    if (options && a === '--') options = false
    else if (options && a.startsWith('-') && a.length > 1) {
      if (takes.has(a)) i++
    } else if (a !== '') out.push(a)
  }

  return out
}

/** The paths a non-git command writes, as written. */
function writeTargets(name: string, args: string[]): string[] {
  switch (name) {
    case 'sed': {
      if (!args.some(a => /^-[a-zA-Z]*i/.test(a) || a.startsWith('--in-place'))) return []
      const scripted = args.some(a => a === '-e' || a === '-f' || a.startsWith('--expression') || a.startsWith('--file'))
      const rest = positionals(args, new Set(['-e', '-f', '--expression', '--file']))
      return scripted ? rest : rest.slice(1)
    }
    case 'perl': {
      if (!args.some(a => /^-[a-zA-Z]*i/.test(a))) return []
      const scripted = args.some(a => /^-[a-zA-Z]*[eE]$/.test(a))
      const rest = positionals(args, new Set(['-e', '-E', '-pe', '-ne', '-pie', '-nie', '-lpe', '-lne']))
      return scripted ? rest : rest.slice(1)
    }
    case 'mv':
    case 'rm':
    case 'rmdir':
    case 'unlink':
    case 'shred':
    case 'tee':
      return [...positionals(args, new Set(['-t', '-S'])), ...optionValue(args, '-t')]
    case 'truncate':
      return positionals(args, new Set(['-s', '-r']))
    case 'cp':
    case 'ln':
    case 'rsync':
    case 'install': {
      const t = optionValue(args, '-t')
      if (t.length > 0) return t
      const rest = positionals(args, new Set(['-t', '-S', '-m', '-o', '-g', '-e']))
      return rest.slice(-1)
    }
    case 'dd':
      return args.filter(a => a.startsWith('of=')).map(a => a.slice(3))
    default:
      return []
  }
}

function optionValue(args: string[], option: string): string[] {
  const i = args.indexOf(option)

  return i >= 0 && i + 1 < args.length ? [args[i + 1]!] : []
}

/**
 * What a git command replaces in the working tree: 'all' (a branch
 * switch, a stash, a hard reset) or the resolved paths it rewrites.
 */
function gitTargets(
  args: string[],
  cwd: string,
  at: (dir: string, word: string) => string,
  exists: (path: string) => boolean,
): 'all' | string[] {
  let dir = cwd
  let i = 0
  while (i < args.length && args[i]!.startsWith('-')) {
    if (args[i] === '-C' && i + 1 < args.length) {
      dir = at(dir, args[i + 1]!)
      i += 2
    } else if (args[i] === '-c') i += 2
    else i++
  }
  const sub = args[i]
  const rest = args.slice(i + 1)
  const dash = rest.indexOf('--')
  const before = dash < 0 ? rest : rest.slice(0, dash)
  const after = dash < 0 ? [] : rest.slice(dash + 1).filter(a => a !== '')
  const paths = (list: string[]) => list.map(p => at(dir, p))
  switch (sub) {
    case 'checkout':
    case 'switch': {
      const takes = new Set(['-b', '-B', '--orphan', '-c', '-C', '--conflict'])
      const created = before.some(a => takes.has(a) && a !== '--conflict')
      const named = positionals(before, takes)
      if (sub === 'switch') return named.length > 0 || before.includes('--orphan') ? 'all' : []
      if (dash >= 0) return paths(after)
      if (named.length === 0) return before.includes('--orphan') ? 'all' : []
      // No `--`: a name that is a path (or a glob, or `.`) is a path; the
      // first that is not is the branch, which replaces the tree.
      const out: string[] = []
      for (const [k, name] of named.entries()) {
        const path = at(dir, name)
        if (GLOB.test(name) || exists(path)) out.push(path)
        else if (k === 0) return 'all'
      }
      return created && out.length === 0 ? [] : out
    }
    case 'restore': {
      const staged = rest.some(a => a === '--staged' || a === '-S' || /^-[a-zA-Z]*S/.test(a))
      const worktree = rest.some(a => a === '--worktree' || a === '-W' || /^-[a-zA-Z]*W/.test(a))
      if (staged && !worktree) return []
      return paths([...positionals(before, new Set(['-s', '--source'])), ...after])
    }
    case 'stash': {
      const action = before.find(a => !a.startsWith('-'))
      if (['list', 'show', 'drop', 'clear', 'create', 'store'].includes(action ?? '')) return []
      if ((action === undefined || action === 'push') && after.length > 0) return paths(after)
      return 'all'
    }
    case 'reset':
      return rest.some(a => a === '--hard' || a === '--merge' || a === '--keep') ? 'all' : []
    case 'clean': {
      const force = rest.some(a => a === '--force' || /^-[a-zA-Z]*f/.test(a))
      const dry = rest.some(a => a === '--dry-run' || /^-[a-zA-Z]*n/.test(a))
      if (!force || dry) return []
      const named = [...positionals(before, new Set(['-e', '--exclude'])), ...after]
      return named.length > 0 ? paths(named) : 'all'
    }
    case 'rm':
    case 'mv':
      return paths([...positionals(before), ...after])
    default:
      return []
  }
}

/**
 * AGENTS.md's `Data:` line. Local dev state is seed data the build
 * expunges freely; `keep` opts a project's local data into the guard.
 * `disposable` is what older projects wrote; null is the default.
 */
export const dataPolicy = (agentsMd: string): 'keep' | 'disposable' | null => {
  const m = agentsMd.match(/^\s*-\s*\*\*Data:\*\*\s*(keep|disposable)\b/im)

  return m ? (m[1]!.toLowerCase() as 'keep' | 'disposable') : null
}

/** The application name `.rbtrc` gives `dev run`, else null. */
export const applicationName = (rbtrc: string): string | null =>
  rbtrc.match(/^\s*dev run\s+--application-name[= ](\S+)/m)?.[1] ?? null
