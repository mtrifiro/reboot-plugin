// Pure logic: a test run as its runner records it in the project's
// `.reboot/test-run.json`, rewritten after each module (the build
// templates' `tests/run_progress.py` for pytest, or a suite script of the
// project's own), and how long each module took in the runs before, which
// tells a stopped run from a slow one. The contract is in the python skill's
// `references/testing-project-setup.md`.

import type { SuiteModule, SuiteRun, SuiteView } from '../types'
import { elapsed } from './deploy'

/** Where a project's runner records its run, from the project's root. */
export const SUITE_FILE = '.reboot/test-run.json'

/** How many finished runs a module's typical time is the median of. */
export const HISTORY_RUNS = 5

/** Each module's seconds in the runs before, oldest first. */
export type History = Record<string, number[]>

const STATUSES = new Set(['pending', 'running', 'passed', 'failed', 'rerun', 'stopped'])

const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const time = (v: unknown): number | null => {
  const t = typeof v === 'string' ? Date.parse(v) : NaN
  return Number.isNaN(t) ? null : t
}

/** The file's run; null when it isn't the contract's shape. */
export function parseSuite(text: string): SuiteRun | null {
  let raw: unknown
  try {
    raw = JSON.parse(text)
  } catch {
    return null
  }
  const r = raw as { started_at?: unknown; finished_at?: unknown; stopped?: unknown; modules?: unknown }
  const startedAt = time(r?.started_at)
  if (startedAt === null || !Array.isArray(r.modules)) return null
  const modules: SuiteModule[] = []
  for (const m of r.modules as Record<string, unknown>[]) {
    if (typeof m?.name !== 'string' || !STATUSES.has(String(m.status))) return null
    modules.push({
      name: m.name,
      status: m.status as SuiteModule['status'],
      passed: num(m.passed),
      failed: num(m.failed),
      skipped: num(m.skipped),
      seconds: num(m.seconds),
      startedAt: time(m.started_at),
    })
  }

  const finishedAt = time(r.finished_at)

  // Stopped: the runner says so, or a module of it was stopped mid-way.
  const isStopped = finishedAt !== null && (r.stopped === true || modules.some(m => m.status === 'stopped'))

  return { startedAt, finishedAt, isStopped, modules }
}

/** The history with a finished run's modules added: each that passed or failed, its last few runs. */
export function remember(h: History, run: SuiteRun): History {
  const next: History = { ...h }
  for (const m of run.modules) {
    if ((m.status === 'passed' || m.status === 'failed') && m.seconds !== null) {
      next[m.name] = [...(h[m.name] ?? []), m.seconds].slice(-HISTORY_RUNS)
    }
  }

  return next
}

/** A module's typical seconds: the median of its runs before; null with none. */
export function typical(h: History, name: string): number | null {
  const xs = [...(h[name] ?? [])].sort((a, b) => a - b)
  if (xs.length === 0) return null
  const mid = Math.floor(xs.length / 2)

  return xs.length % 2 ? xs[mid]! : (xs[mid - 1]! + xs[mid]!) / 2
}

/**
 * How long a run the band saw in `ps` may be gone from it, its file
 * unchanged, before it counts as stopped: two polls, so a suite script
 * starting its next pytest isn't caught between modules.
 */
export const STOPPED_AFTER_MS = 10_000

/**
 * How long a run the band never saw in `ps` may go with its file
 * unchanged before it counts as stopped: twice the running module's
 * typical time, ten minutes at least. Such a runner may be one `ps`
 * doesn't show as a test run, so it gets the benefit of the doubt.
 */
const UNSEEN_MS = 10 * 60 * 1000

/**
 * The run as the band treats it. One its runner left without an end
 * (killed, so no end-of-run hook ran) counts as stopped once no test
 * runs in `ps` and its file is unchanged: soon after the band last saw
 * it running (`seenTestingAt`), or, never seen, after the long wait. A
 * stopped run ends when it was last written or seen, whichever is later,
 * and its running module is the stopped one.
 */
export function settle(
  run: SuiteRun,
  at: { now: number; writtenAt: number; seenTestingAt: number | null; isTesting: boolean; history: History },
): SuiteRun {
  if (run.finishedAt !== null || at.isTesting) return run
  const lastSign = Math.max(at.writtenAt, at.seenTestingAt ?? 0)
  const running = run.modules.find(m => m.status === 'running')
  const t = running ? typical(at.history, running.name) : null
  const wait = at.seenTestingAt !== null ? STOPPED_AFTER_MS : Math.max(UNSEEN_MS, 2 * (t ?? 0) * 1000)
  if (at.now - lastSign <= wait) return run

  return {
    ...run,
    finishedAt: lastSign,
    isStopped: true,
    modules: run.modules.map(m => (m.status === 'running' ? { ...m, status: 'stopped' } : m)),
  }
}

/** Whether the band shows the run: a running one; an ended one, finished or stopped, until code changes after it. */
export function isSuiteShown(run: SuiteRun, at: { lastEditAt: number }): boolean {
  return run.finishedAt === null || at.lastEditAt <= run.finishedAt
}

/** `11:49`: a clock time, local, on the 12-hour clock the way a person says it. */
export function clockTime(ms: number): string {
  const d = new Date(ms)

  return `${d.getHours() % 12 || 12}:${String(d.getMinutes()).padStart(2, '0')}`
}

/** `1,032`: a count with its thousands marked. */
const count = (n: number): string => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',')

/**
 * The tests so far, across the modules that ran or run now: `958 passed,
 * 1 skipped, 0 failed`, the modules that failed named after
 * (`1 failed (web_test)`), and reruns apart (`1 rerun`). A failed module
 * that gave no count counts one.
 */
function tally(run: SuiteRun): string {
  const sum = (f: (m: SuiteModule) => number) => run.modules.reduce((n, m) => n + f(m), 0)
  const failedModules = run.modules.filter(m => m.status === 'failed').map(m => m.name)
  const failed = sum(m => m.failed ?? (m.status === 'failed' ? 1 : 0))
  const reruns = run.modules.filter(m => m.status === 'rerun').length
  const parts = [`${count(sum(m => m.passed ?? 0))} passed`]
  const skipped = sum(m => m.skipped ?? 0)
  if (skipped > 0) parts.push(`${count(skipped)} skipped`)
  parts.push(failedModules.length > 0 ? `${count(failed)} failed (${failedModules.join(', ')})` : `${count(failed)} failed`)
  if (reruns > 0) parts.push(`${reruns} rerun`)

  return parts.join(', ')
}

/** How far the run is for a line that already says what the turn does: `7 of 20 modules`. */
export function suiteStatus(view: SuiteView): string {
  const { modules } = view.run
  const done = modules.filter(m => m.status === 'passed' || m.status === 'failed' || m.status === 'rerun').length

  return `${done} of ${modules.length} modules`
}

/**
 * The band's two rows for a run. While it goes, what is done and what is
 * left, with no guess at when it ends (history made a poor one):
 *
 *     So far: 11 of 20 modules, 958 passed, 1 skipped, 0 failed
 *     Left: 9 modules
 *
 * Once it ends, the result and its time:
 *
 *     Done: 20 modules, 1,032 passed, 1 skipped, 1 failed (web_test)
 *     Took 23m 52s, finished at 11:49
 *
 * Or, stopped before its end, how far it got:
 *
 *     Stopped: 11 of 20 modules, 958 passed, 1 skipped, 0 failed
 *     Ran 6m 10s, stopped at 11:31
 */
export function suiteLine(view: SuiteView, clock: (ms: number) => string = clockTime): string {
  const { run } = view
  if (run.finishedAt === null) {
    const left = run.modules.filter(m => m.status === 'pending' || m.status === 'running').length
    return `So far: ${suiteStatus(view)}, ${tally(run)}\nLeft: ${left} ${left === 1 ? 'module' : 'modules'}`
  }

  if (run.isStopped) {
    return (
      `Stopped: ${suiteStatus(view)}, ${tally(run)}\n` +
      `Ran ${elapsed(run.finishedAt - run.startedAt)}, stopped at ${clock(run.finishedAt)}`
    )
  }

  return (
    `Done: ${run.modules.length} modules, ${tally(run)}\n` +
    `Took ${elapsed(run.finishedAt - run.startedAt)}, finished at ${clock(run.finishedAt)}`
  )
}
