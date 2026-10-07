// Pure logic: what an API file declares, and which changes between two
// versions of it the runtime refuses over persisted state. Follows the
// table in skills/python/references/api-schema-evolution.md. Regex, not
// a parser: it reads the shape the build templates write.

export type Schema = {
  /** Model class → field tag → `name: type`. */
  models: Map<string, Map<number, { name: string; type: string }>>
  /** State Type → method name → { kind, description }. */
  types: Map<string, Map<string, { kind: string; description: string | null }>>
}

const STRING = String.raw`(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')`
const DESCRIPTION = new RegExp(String.raw`description\s*=\s*\(?((?:\s*${STRING})+)`)
const METHOD = /(\w+)\s*=\s*(Reader|Writer|Transaction|Workflow|UI)\s*\(/g
const TYPE = /(\w+)\s*=\s*Type\s*\(/g

/** The text of adjacent string literals, quotes and joins removed. */
const literal = (s: string) =>
  [...s.matchAll(new RegExp(STRING, 'g'))].map(m => m[0].slice(1, -1)).join('')

export function parse(text: string): Schema {
  const models: Schema['models'] = new Map()
  for (const block of text.split(/^(?=class\s)/m)) {
    const cls = block.match(/^class\s+(\w+)\s*\(/)
    if (!cls) continue
    const fields = new Map<number, { name: string; type: string }>()
    for (const f of block.matchAll(/^\s+(\w+)\s*:\s*([^=\n]+?)\s*=\s*Field\(([^)]*)/gm)) {
      const tag = f[3]!.match(/\btag\s*=\s*(\d+)/)
      if (tag) fields.set(Number(tag[1]), { name: f[1]!, type: f[2]!.replace(/\s+/g, '') })
    }
    models.set(cls[1]!, fields)
  }

  const types: Schema['types'] = new Map()
  const typeStarts = [...text.matchAll(TYPE)]
  typeStarts.forEach((t, i) => {
    const body = text.slice(t.index!, typeStarts[i + 1]?.index ?? text.length)
    const methods = new Map<string, { kind: string; description: string | null }>()
    const calls = [...body.matchAll(METHOD)]
    calls.forEach((m, j) => {
      const call = body.slice(m.index!, calls[j + 1]?.index ?? body.length)
      const d = call.match(DESCRIPTION)
      methods.set(m[1]!, { kind: m[2]!, description: d ? literal(d[1]!) : null })
    })
    types.set(t[1]!, methods)
  })

  return { models, types }
}

const COMPATIBLE_KINDS = new Set(['Reader:Reader', 'Writer:Transaction', 'Transaction:Writer'])

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
      if (n.kind !== m.kind && !COMPATIBLE_KINDS.has(`${m.kind}:${n.kind}`)) {
        problems.push(`method \`${type}.${name}\` changes kind, ${m.kind} → ${n.kind}`)
      }
      if (m.description !== null && n.description !== m.description) {
        problems.push(`method \`${type}.${name}\`'s \`description=\` changes`)
      }
    }
  }

  // A renamed model class is compatible; pair one gone with one new.
  const gone = [...a.models.keys()].filter(c => !b.models.has(c))
  const added = [...b.models.keys()].filter(c => !a.models.has(c))
  const renamed = gone.length === 1 && added.length === 1 ? new Map([[gone[0]!, added[0]!]]) : null

  for (const [cls, fields] of a.models) {
    const next = b.models.get(renamed?.get(cls) ?? cls)
    if (!next) continue // the class itself is gone; its Type's methods say whether that matters
    for (const [tag, f] of fields) {
      const n = next.get(tag)
      if (!n) problems.push(`field \`${cls}.${f.name}\` (tag ${tag}) is deleted or its tag changed`)
      else if (n.type !== f.type) {
        problems.push(`field \`${cls}.${f.name}\` (tag ${tag}) changes type, ${f.type} → ${n.type}`)
      }
    }
  }

  return problems
}

/** An API definition file the build writes, not generated code. */
export const isApiFile = (path: string): boolean =>
  /\/api\/[^/]+\/v1\/[^/]+\.py$/.test(path) &&
  !/_rbt\.py$/.test(path) &&
  !/\/(backend|frontend|web)\/[^]*api\//.test(path)

/** The application name `.rbtrc` gives `dev run`, else null. */
export const applicationName = (rbtrc: string): string | null =>
  rbtrc.match(/^\s*dev run\s+--application-name[= ](\S+)/m)?.[1] ?? null
