// Pure logic: which step a tool call shows, how the current task moves
// through its steps, and which processes are up. Kept free of `$` so the tests can call it directly.

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

/**
 * The Reboot Flywheel stage a step belongs to: Design until the data
 * model is accepted, Prove from the project shell on. A deploy is
 * Promote, which the band shows while one runs.
 */
export function stageOf(step: number): 'Design' | 'Prove' {
  return step <= 1 ? 'Design' : 'Prove'
}

/**
 * The stage in front of the band's sentence: Promote while a deploy runs;
 * none without a task under way; Prove while the sentence is a test run,
 * which is Prove whatever step the task's evidence has reached (a task
 * that changed only config, or a prompt read as new work, is still at
 * Planning); else the task's own stage.
 */
export function lineStage(
  t: { step: number; isDone: boolean } | null,
  o: { isDeploying: boolean; isTestLine: boolean },
): 'Design' | 'Prove' | 'Promote' | null {
  if (o.isDeploying) return 'Promote'
  if (t === null || t.isDone) return null
  return o.isTestLine ? 'Prove' : stageOf(t.step)
}

/** The review table the build skill shows at its checkpoint: its header row. */
const REVIEW_TABLE = /\|\s*State type\s*\|\s*State ID\s*\|\s*Rule\s*\|/

/** Whether narration holds the design review the user is asked to accept. */
export function isReviewTable(text: string): boolean {
  return REVIEW_TABLE.test(text)
}

/** The card's header line for a task that just finished, by its kind. */
export function finishedToast(kind: TaskKind): string {
  return kind === 'build'
    ? 'The prototype is built and tested'
    : kind === 'feature'
      ? 'The feature is built and tested'
      : 'The fix is in'
}
const BACKEND = 3
const SCREENS = 5
const TESTS = 6

/** The kind of work a task is: a whole new app, a feature, or a bug fix. */
export type TaskKind = 'build' | 'feature' | 'fix'

export type Call =
  | { tool: 'Skill'; skill: string }
  | { tool: 'Bash'; command: string }
  | { tool: 'Write' | 'Edit'; file_path: string; text: string }

/** The kind of task a skill starts: the build skills a build, `feature` a feature. */
export function skillKind(skill: string): TaskKind | null {
  if (/^(reboot:)?(app|build|mcp-ui|web-app)$/.test(skill)) return 'build'
  if (/^(reboot:)?feature$/.test(skill)) return 'feature'
  return null
}

/**
 * The kind of task a prompt the person typed starts by its slash command
 * (`/reboot:app build a todo app`). Namespaced only: a bare `/app` may be
 * another plugin's.
 */
export function commandKind(text: string): TaskKind | null {
  const m = text.match(/^\s*\/(reboot:[\w-]+)(\s|$)/)

  return m ? skillKind(m[1]!) : null
}

/**
 * The step a call is evidence of, or null when it says nothing.
 * Paths follow the layouts in the mcp-ui and web-app skills.
 */
export function stepOf(call: Call): number | null {
  if (call.tool === 'Skill') {
    return skillKind(call.skill) !== null ? 0 : null
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
}

/** The band's links: the developer dashboard and the app's front end, while each serves. */
export type Links = { dashboard: string | null; app: string | null }

/** `rbt dashboard`'s own default port, for a project whose `.rbtrc` names none. */
export const DASHBOARD_PORT = 9871

/**
 * The links for an app: the dashboard while it listens; the front end a
 * person opens: the browser SPA's page where the app has one, else (an
 * MCP UI alone) the setup wizard at the backend's root.
 */
export function appLinks(
  ports: Set<number>,
  app: { backendPort: number; dashboardPort: number; vitePort: number | null; hasWebApp: boolean },
): Links {
  const dashboard = ports.has(app.dashboardPort) ? `http://127.0.0.1:${app.dashboardPort}/` : null
  if (app.hasWebApp) {
    return { dashboard, app: app.vitePort !== null ? `http://localhost:${app.vitePort}/` : null }
  }

  return { dashboard, app: ports.has(app.backendPort) ? `http://localhost:${app.backendPort}/` : null }
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

/**
 * The dashboard's port: `dashboard --port=N` in `.rbtrc` (where this
 * project's dashboard starts), else `dev run --dashboard-port=N` (where
 * its dev loop looks for it), else `rbt dashboard`'s default.
 */
export function dashboardPort(rbtrc: string): number {
  const m = rbtrc.match(/^\s*dashboard\s+--port[= ](\d+)/m) ?? rbtrc.match(/^\s*dev run\s+--dashboard-port[= ](\d+)/m)

  return m ? Number(m[1]) : DASHBOARD_PORT
}

/**
 * The port this project's Vite serves on, read from the running process,
 * not a config: a `vite` in `ps -axo pid=,command=` output whose command
 * names a path in `dir`, and the lowest port it listens on in `lsof -nP
 * -iTCP -sTCP:LISTEN` output; null while none runs. A test suite's Vite
 * (`--strictPort` on a port of its own) and `vite preview` are not the
 * one a person opens.
 */
export function vitePortOf(lsof: string, ps: string, dir: string): number | null {
  const pids = new Set<number>()
  for (const line of ps.split('\n')) {
    const m = line.match(/^\s*(\d+)\s+(.*)$/)
    const isDev = m && /\bvite\b/.test(m[2]!) && !/--strictPort|\bvite\s+preview\b/.test(m[2]!)
    if (m && isDev && m[2]!.includes(`${dir}/`)) pids.add(Number(m[1]))
  }
  const ports: number[] = []
  for (const m of lsof.matchAll(/^.+?\s+(\d+)\s+\S+\s+\S+\s+IPv[46]\b.*:(\d+) \(LISTEN\)$/gm)) {
    if (pids.has(Number(m[1]))) ports.push(Number(m[2]))
  }

  return ports.length > 0 ? Math.min(...ports) : null
}

export type Task = { kind: TaskKind; step: number; isDone: boolean; isRestored?: boolean }

/**
 * The task after a skill (or a typed slash command) of `kind`: a new one,
 * unless this session has a task under way, which the skill is part of
 * (the build flow calls the feature skill for its spec; an update enters
 * the build skill). One restored from an earlier session doesn't count.
 */
export const beginTask = (t: Task | null, kind: TaskKind): Task =>
  t && !t.isDone && !t.isRestored ? t : { kind, step: 0, isDone: false }

/** What the prompt summary says a request is: new work of a kind, or the same work. */
export type Decision = TaskKind | 'same'

/**
 * The task after the person's prompt, as the summary judged it. A follow-up
 * keeps the task; new work starts one, except new work of the same kind
 * while this session's task of that kind is under way, which is most likely
 * an answer or approval read as new ("yes, build it").
 */
export function taskAfterPrompt(t: Task | null, decision: Decision | null): Task | null {
  if (decision === null || decision === 'same') return t
  if (t && !t.isDone && !t.isRestored && t.kind === decision) return t

  return { kind: decision, step: 0, isDone: false }
}

/**
 * The task after a call that is evidence of `step`: forward only, and only
 * when the step means real progress for that kind of task. With no task,
 * evidence starts none: the prompt or a skill does.
 */
export function advanceTask(t: Task | null, step: number): Task | null {
  if (t === null || t.isDone) return t
  // A task restored from an earlier session may be stale or wrong: the
  // first evidence in this session says where it really is.
  if (t.isRestored) return { kind: t.kind, step, isDone: false }
  // A build writes its spec's test module right after planning and starts
  // the app mid-build to check its work: tests count once the backend
  // exists, Launch once the screens do. A feature or fix tests once it has
  // changed code, and starting the app counts only after its tests.
  const hasCode = t.kind === 'build' ? t.step >= BACKEND : t.step >= 1
  if (step === TESTS && !hasCode) return t
  if (step === RUN && t.step < (t.kind === 'build' ? SCREENS : TESTS)) return t

  return { kind: t.kind, step: Math.max(t.step, step), isDone: false }
}

/**
 * The end of a turn finishes a task that reached its last step: Launch for
 * a build, its tests for a feature or fix.
 */
export function finishTurn(t: Task | null): Task | null {
  if (t === null || t.isDone) return t
  const last = t.kind === 'build' ? RUN : TESTS

  return t.step >= last ? { kind: t.kind, step: t.step, isDone: true } : t
}

/** The `$.store` key holding a project's task across sessions. */
export const storeKey = (root: string): string => `build:${root}`

/** A stored value, if it is a task. Values stored before kinds count as builds. */
export function asTask(value: unknown): Task | null {
  if (typeof value !== 'object' || value === null) return null
  const { kind, step, isDone } = value as Record<string, unknown>
  const k: TaskKind = kind === 'feature' || kind === 'fix' ? kind : 'build'

  return typeof step === 'number' && step >= 0 && step <= RUN && typeof isDone === 'boolean'
    ? { kind: k, step, isDone }
    : null
}

/** The current task in a few words, for the prompt summary to judge follow-ups by. */
export function describeTask(t: Task | null): string {
  if (t === null || t.isDone) return 'none'
  const what = { build: 'building a new app', feature: 'adding a feature', fix: 'fixing a bug' }[t.kind]

  return `${what}, at the ${STEPS[t.step]!.toLowerCase()} step`
}

/**
 * What a poll has seen of one server: whether it was last announced up
 * (null before the first poll), and how many polls in a row have disagreed.
 */
export type Watch = { isUp: boolean | null; misses: number }

export const UNWATCHED: Watch = { isUp: null, misses: 0 }

/**
 * Polls in a row a server must be down before its stop is announced.
 * `rbt dev run` restarts the backend on each save, which reads as down for
 * a poll or two; a stop that lasts three (15 seconds) is real.
 */
export const STOP_POLLS = 3

/**
 * The watch after a poll, and the change to announce, if any. The first poll
 * only learns the state: a server already running when the session starts
 * isn't news. A start counts at once; a stop once it lasts STOP_POLLS.
 */
export function observe(w: Watch, isUp: boolean): { watch: Watch; change: 'started' | 'stopped' | null } {
  if (w.isUp === null || w.isUp === isUp) return { watch: { isUp, misses: 0 }, change: null }
  if (isUp) return { watch: { isUp, misses: 0 }, change: 'started' }
  const misses = w.misses + 1

  return misses >= STOP_POLLS
    ? { watch: { isUp: false, misses: 0 }, change: 'stopped' }
    : { watch: { isUp: true, misses }, change: null }
}
