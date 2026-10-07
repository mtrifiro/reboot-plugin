// Pure logic: which build step a tool call shows, and how the status
// line reads. Kept free of `$` so the tests can call it directly.

export const STEPS = [
  'Planning', // design: agree on the app before any code
  'Data model', // the API definition
  'Setup', // the project shell from a template
  'Backend', // the servicers
  'Access rules', // the authorizers
  'Screens', // the frontend
  'Tests',
  'Launch', // rbt dev run
] as const

export const RUN = STEPS.length - 1

/** The major steps the bar fills by, each covering one or more of STEPS. */
export const MAJOR_STEPS: readonly (readonly number[])[] = [
  [0], // planning
  [1, 2], // data model, setup
  [3, 4], // backend, access rules
  [5], // screens
  [6], // tests
  [7], // launch
]

/** The major step a step belongs to, by index. */
export const majorOf = (step: number): number =>
  Math.max(0, MAJOR_STEPS.findIndex(steps => steps.includes(step)))
const BACKEND = 3
const TESTS = 6

// The skills that start (or re-enter) the build flow.
const BUILD_SKILL = /^(reboot:)?(app|build|mcp-ui|web-app)$/

export type Call =
  | { tool: 'Skill'; skill: string }
  | { tool: 'Bash'; command: string }
  | { tool: 'Write' | 'Edit'; file_path: string; text: string }

export const isBuildSkill = (skill: string): boolean => BUILD_SKILL.test(skill)

/**
 * The build step a call is evidence of, or null when it says nothing.
 * Paths follow the layouts in the mcp-ui and web-app skills.
 */
export function stepOf(call: Call): number | null {
  if (call.tool === 'Skill') {
    return isBuildSkill(call.skill) ? 0 : null
  }
  if (call.tool === 'Bash') {
    const c = call.command
    if (/\brbt\s+dev\s+run\b/.test(c)) return 7
    if (/\bpytest\b/.test(c)) return 6
    if (/\bcopy\.sh\b|\brbt\s+generate\b|\buv\s+sync\b/.test(c)) return 2
    return null
  }
  const p = call.file_path
  // Generated code is never evidence of a step.
  if (/_rbt\.py$|\/node_modules\/|\/dist\//.test(p)) return null
  // Feature files are the agreed spec, written right after Planning
  // (the feature skill), so they say nothing about Tests; test code does.
  if (/\.feature$/.test(p)) return null
  if (/\/tests\/[^/]*_test\.py$/.test(p)) return 6
  if (/\/backend\/src\/servicers\/[^/]+\.py$/.test(p)) {
    return /\bdef authorizer\s*\(/.test(call.text) ? 4 : 3
  }
  if (/\/backend\/src\/(main|example_prompts)\.py$/.test(p)) return 2
  if (/\/(frontend|web)\/(?!(.*\/)?api\/)/.test(p)) return 5
  if (/\/api\/[^/]+\/v1\/[^/]+\.py$/.test(p) && !/\/(backend|frontend|web)\//.test(p)) {
    return 1
  }
  return null
}

export type Health = {
  backend: boolean
  frontend: boolean | null // null: the app has no frontend
  tunnel: boolean | null // null: not an MCP app, so no tunnel
  url: string | null
}

const dot = (isUp: boolean) => (isUp ? '●' : '○')

export function formatStatus(h: Health): string {
  const parts = [`rbt ${dot(h.backend)}`]
  if (h.frontend !== null) parts.push(`web ${dot(h.frontend)}`)
  if (h.tunnel !== null) parts.push(`tunnel ${dot(h.tunnel)}`)
  const line = parts.join('  ')

  return h.url ? `${line}  ${h.url}` : line
}

/** Ports in LISTEN state from `lsof -nP -iTCP -sTCP:LISTEN` output. */
export function listeningPorts(lsof: string): Set<number> {
  const ports = new Set<number>()
  for (const m of lsof.matchAll(/:(\d+) \(LISTEN\)/g)) ports.add(Number(m[1]))

  return ports
}

/** The backend port: `dev run --port=N` in `.rbtrc`, else 9991. */
export function backendPort(rbtrc: string): number {
  const m = rbtrc.match(/^\s*dev run\s+--port[= ](\d+)/m)

  return m ? Number(m[1]) : 9991
}

/** The cloudflared metrics port from a `ps` command line, else null. */
export function metricsPort(ps: string): number | null {
  const line = ps.split('\n').find(l => /cloudflared/.test(l) && /\btunnel\b/.test(l))
  if (!line) return null
  const m = line.match(/--metrics[= ](?:[\w.]+)?:(\d+)/)

  return m ? Number(m[1]) : 4040
}

export type Bar = {
  /** Filled cells, then empty ones; together `width`. */
  filled: number
  empty: number
}

/**
 * The progress bar for a build at `step`, over the major steps: those
 * before the current one count as done, so planning shows an empty bar
 * and a finished build a full one.
 */
export function progressBar(step: number, isDone: boolean, width: number): Bar {
  const major = majorOf(step)
  const done = isDone ? MAJOR_STEPS.length : major
  const filled = Math.round((done / MAJOR_STEPS.length) * width)

  return { filled, empty: width - filled }
}

/** Bar cells for a band `columns` wide: what its label leaves, 10 to 40. */
export const barWidth = (columns: number): number =>
  Math.max(10, Math.min(40, columns - 'Reboot  '.length))

export type BuildState = { step: number; isDone: boolean; isRestored?: boolean }

/**
 * The build after a call that is evidence of `step`. A build skill opens
 * a new build unless this session has one under way (one restored from an
 * earlier session doesn't count: the skill means a new flow); other
 * evidence moves a build
 * forward only, and starts one when none is known (a session resumed
 * mid-build without the skill), short of Run, which a finished app's
 * restart also shows.
 */
export function nextBuild(
  b: BuildState | null,
  step: number,
  isBuildSkillCall: boolean,
): BuildState | null {
  if (isBuildSkillCall) return b && !b.isDone && !b.isRestored ? b : { step: 0, isDone: false }
  // The spec's test module is written right after Planning (the feature
  // skill), so test evidence counts only once the backend exists.
  if (step === TESTS && (b === null || b.step < BACKEND)) return b
  if (b === null) return step >= 1 && step < RUN ? { step, isDone: false } : null
  if (b.isDone) return b
  // A build restored from an earlier session may be stale or wrong: the
  // first evidence in this session says where it really is.
  if (b.isRestored) return { step, isDone: false }

  // Starting the app is Launch, not done: the model runs it mid-build too.
  return { step: Math.max(b.step, step), isDone: false }
}

/** The end of a turn finishes a build that reached Launch; anything else stays. */
export const finishTurn = (b: BuildState | null): BuildState | null =>
  b !== null && !b.isDone && b.step === RUN ? { step: RUN, isDone: true } : b

/** The `$.store` key holding a project's build across sessions. */
export const storeKey = (root: string): string => `build:${root}`

/** A stored value, if it is a build. */
export function asBuild(value: unknown): BuildState | null {
  if (typeof value !== 'object' || value === null) return null
  const { step, isDone } = value as Record<string, unknown>

  return typeof step === 'number' && step >= 0 && step <= RUN && typeof isDone === 'boolean'
    ? { step, isDone }
    : null
}

// The bar's gradient: orange at its left end to green at its right, by hue
// (through yellow) so the middle stays bright rather than olive.
const FROM = { h: 25, s: 95, l: 53 } // orange, about #F97316
const TO = { h: 142, s: 71, l: 45 } // green, about #22C55E

function hex(h: number, s: number, l: number): string {
  const a = (s / 100) * Math.min(l / 100, 1 - l / 100)
  const channel = (n: number) => {
    const k = (n + h / 30) % 12
    const v = l / 100 - a * Math.max(-1, Math.min(k - 3, 9 - k, 1))
    return Math.round(v * 255).toString(16).padStart(2, '0')
  }

  return `#${channel(0)}${channel(8)}${channel(4)}`
}

/**
 * The filled cells as runs of one color each, left to right. A cell's color
 * is its place along the whole bar, so a short fill is all orange and a
 * full bar sweeps to green.
 */
export function barRuns(filled: number, width: number): { color: string; cells: number }[] {
  const runs: { color: string; cells: number }[] = []
  for (let i = 0; i < filled; i++) {
    const t = width <= 1 ? 1 : i / (width - 1)
    const color = hex(
      FROM.h + (TO.h - FROM.h) * t,
      FROM.s + (TO.s - FROM.s) * t,
      FROM.l + (TO.l - FROM.l) * t,
    )
    const last = runs[runs.length - 1]
    if (last && last.color === color) last.cells += 1
    else runs.push({ color, cells: 1 })
  }

  return runs
}
