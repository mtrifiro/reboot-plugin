// Pure logic: what an API file declares, and which changes between two
// versions of it the runtime refuses over persisted state. Follows the
// table in skills/python/references/api-schema-evolution.md. Regex, not
// a parser: it reads the shape the build templates write.

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
 * move, copy, tee or delete of it, or a git checkout, restore or stash
 * that would replace it. Reading one (`cat`, `grep`, `sed -n`) is not.
 */
export function bashEditsApi(command: string): boolean {
  const api = String.raw`\S*api/[\w.-]+/v1/[\w.-]+\.py\b`
  if (!new RegExp(api).test(command)) return false
  const writes = [
    String.raw`\bsed\s+(-\S*\s+)*-i`,
    String.raw`\bperl\s+(-\S*\s+)*-\S*i`,
    String.raw`>>?\s*${api}`,
    String.raw`\b(mv|cp|rm|tee)\b[^|;&\n]*${api}`,
    String.raw`\bgit\s+(checkout|restore|stash)\b[^|;&\n]*${api}`,
  ]

  return writes.some(w => new RegExp(w).test(command))
}

/** The application name `.rbtrc` gives `dev run`, else null. */
export const applicationName = (rbtrc: string): string | null =>
  rbtrc.match(/^\s*dev run\s+--application-name[= ](\S+)/m)?.[1] ?? null
