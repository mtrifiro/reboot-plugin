// Pure logic: a test run as its runner records it in the project's
// `.reboot/test-run.json`, rewritten after each module (the build
// templates' `tests/run_progress.py` for pytest, or a suite script of the
// project's own), how long each module took in the runs before, and when
// this one should end. The contract is in the python skill's
// `references/testing-project-setup.md`.

import type { SuiteModule, SuiteRun, SuiteView } from '../types'
import { elapsed } from './deploy'

/** Where a project's runner records its run, from the project's root. */
export const SUITE_FILE = '.reboot/test-run.json'

/** How many finished runs a module's typical time is the median of. */
export const HISTORY_RUNS = 5

/** Each module's seconds in the runs before, oldest first. */
export type History = Record<string, number[]>

const STATUSES = new Set(['pending', 'running', 'passed', 'failed', 'rerun'])

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
  const r = raw as { started_at?: unknown; finished_at?: unknown; modules?: unknown }
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
      seconds: num(m.seconds),
      startedAt: time(m.started_at),
    })
  }

  return { startedAt, finishedAt: time(r.finished_at), modules }
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
 * When a running run should end: now, plus what the running module's
 * typical time leaves (floored at 0), plus each pending module's typical
 * time. Null when any of them has no history: no time is better than an
 * invented one. A module that doesn't say when it started is taken to
 * have started when the modules before it, one after another, ended.
 */
export function expectedFinish(run: SuiteRun, h: History, now: number): number | null {
  let left = 0
  let doneSeconds = 0
  for (const m of run.modules) {
    if (m.status === 'pending' || m.status === 'running') {
      const t = typical(h, m.name)
      if (t === null) return null
      const since = m.startedAt ?? run.startedAt + doneSeconds * 1000
      left += m.status === 'running' ? Math.max(0, t - (now - since) / 1000) : t
    } else {
      doneSeconds += m.seconds ?? 0
    }
  }

  return now + left * 1000
}

/** How long a run whose file stopped changing may go before it counts as abandoned. */
const ABANDONED_MS = 10 * 60 * 1000

/**
 * Whether the band shows the run: a finished one until code changes
 * after it; a running one unless it was abandoned (killed, the machine
 * asleep): no test run in `ps` and its file unchanged for twice the
 * running module's typical time, ten minutes at least.
 */
export function isSuiteShown(
  run: SuiteRun,
  at: { now: number; writtenAt: number; lastEditAt: number; isTesting: boolean; history: History },
): boolean {
  if (run.finishedAt !== null) return at.lastEditAt <= run.finishedAt
  if (at.isTesting) return true
  const running = run.modules.find(m => m.status === 'running')
  const t = running ? typical(at.history, running.name) : null

  return at.now - at.writtenAt <= Math.max(ABANDONED_MS, 2 * (t ?? 0) * 1000)
}

/** `11:49`: a clock time, local, on the 12-hour clock the way a person says it. */
export function clockTime(ms: number): string {
  const d = new Date(ms)

  return `${d.getHours() % 12 || 12}:${String(d.getMinutes()).padStart(2, '0')}`
}

/** `1 failed: web_test`, `2 failed: leads_test, web_test`; '' when none. */
function failures(run: SuiteRun): string {
  const failed = run.modules.filter(m => m.status === 'failed').map(m => m.name)

  return failed.length === 0 ? '' : `${failed.length} failed: ${failed.join(', ')}`
}

/** How far the run is for a line that already says what the turn does: `7 of 20 modules`. */
export function suiteStatus(view: SuiteView): string {
  const { modules } = view.run
  const done = modules.filter(m => m.status !== 'pending' && m.status !== 'running').length

  return `${done} of ${modules.length} modules`
}

/**
 * The band's line for a run. While it goes: `Tests · 7 of 20 modules ·
 * 0 failed · done ≈ 11:49`, the finish only with history. Once it ends:
 * `Tests passed · 20 modules · 23m 52s`, or `Tests failed · 1 failed:
 * web_test · …`. A rerun (a harness failure) is named apart from failures.
 */
export function suiteLine(view: SuiteView, clock: (ms: number) => string = clockTime): string {
  const { run, expectedAt } = view
  const reruns = run.modules.filter(m => m.status === 'rerun').length
  const rerun = reruns > 0 ? `${reruns} rerun` : ''
  if (run.finishedAt === null) {
    const finish = expectedAt === null ? '' : `done ≈ ${clock(expectedAt)}`
    return ['Tests', suiteStatus(view), failures(run) || '0 failed', rerun, finish].filter(Boolean).join(' · ')
  }
  const failed = failures(run)

  return [
    failed ? 'Tests failed' : 'Tests passed',
    failed,
    `${run.modules.length} modules`,
    rerun,
    elapsed(run.finishedAt - run.startedAt),
  ]
    .filter(Boolean)
    .join(' · ')
}
