import { describe, expect, test } from 'claude-code/testing'

import { isSuiteShown, parseSuite, remember, settle, STOPPED_AFTER_MS, suiteLine, typical } from './suite'

const T0 = Date.parse('2026-10-08T11:24:00-05:00')
const at = (s: number) => new Date(T0 + s * 1000).toISOString()

const FILE = JSON.stringify({
  started_at: at(0),
  finished_at: null,
  modules: [
    { name: 'accounts_test', status: 'passed', passed: 114, failed: 0, seconds: 130.1 },
    { name: 'leads_test', status: 'running' },
    { name: 'web_test', status: 'pending' },
  ],
})
const clock = (ms: number) => `+${Math.round((ms - T0) / 1000)}s`

describe('the run file', () => {
  test('reads the contract, and nothing else', () => {
    const run = parseSuite(FILE)!
    expect(run.startedAt).toBe(T0)
    expect(run.finishedAt).toBe(null)
    expect(run.modules.map(m => m.status)).toEqual(['passed', 'running', 'pending'])
    expect(run.modules[0]!.seconds).toBe(130.1)
    expect(parseSuite('not json')).toBe(null)
    expect(parseSuite('{"started_at": "x", "modules": []}')).toBe(null)
    expect(parseSuite(JSON.stringify({ started_at: at(0), modules: [{ name: 'a', status: 'odd' }] }))).toBe(null)
    expect(run.isStopped).toBe(false)
  })

  test('a run its runner ended with a module stopped is a stopped run', () => {
    const stopped = JSON.stringify({
      started_at: at(0),
      finished_at: at(200),
      modules: [
        { name: 'accounts_test', status: 'passed', passed: 114, failed: 0, seconds: 130.1 },
        { name: 'leads_test', status: 'stopped', passed: 3, failed: 0, seconds: 69.9 },
        { name: 'web_test', status: 'pending' },
      ],
    })
    const run = parseSuite(stopped)!
    expect(run.isStopped).toBe(true)
    expect(run.finishedAt).toBe(T0 + 200_000)
    // Stopped between modules: no module to mark, so the run says it.
    const between = JSON.stringify({ started_at: at(0), finished_at: at(140), stopped: true, modules: [
      { name: 'accounts_test', status: 'passed', passed: 114, failed: 0, seconds: 130.1 },
      { name: 'web_test', status: 'pending' },
    ] })
    expect(parseSuite(between)!.isStopped).toBe(true)
  })
})

describe('the history', () => {
  test("keeps each module's last five runs, its typical time their median", () => {
    let h = {}
    for (const s of [100, 300, 200, 900, 250, 260]) {
      h = remember(h, { startedAt: 0, finishedAt: 1, isStopped: false, modules: [{ name: 'a', status: 'passed', passed: 1, failed: 0, skipped: null, seconds: s, startedAt: null }] })
    }
    expect((h as Record<string, number[]>).a).toEqual([300, 200, 900, 250, 260])
    expect(typical(h, 'a')).toBe(260)
    expect(typical(h, 'none')).toBe(null)
  })
})

describe('the line', () => {
  test('while it goes: what is done, then what is left, with no finish time', () => {
    const run = parseSuite(FILE)!
    run.modules[0]!.skipped = 1
    expect(suiteLine({ run }, clock)).toBe(
      'So far: 1 of 3 modules, 114 passed, 1 skipped, 0 failed\nLeft: 2 modules',
    )
  })

  test('names failed modules at once, and a rerun apart from failures', () => {
    const run = parseSuite(FILE)!
    run.modules[0]!.status = 'failed'
    run.modules[0]!.failed = 2
    run.modules[1]!.status = 'rerun'
    expect(suiteLine({ run }, clock)).toBe(
      'So far: 2 of 3 modules, 114 passed, 2 failed (accounts_test), 1 rerun\nLeft: 1 module',
    )
  })

  test('once it ends: the result, its time, and when it finished', () => {
    const run = parseSuite(FILE)!
    run.finishedAt = T0 + 1432_000
    run.modules.forEach(m => {
      m.status = 'passed'
      m.passed = m.passed ?? 459
    })
    expect(suiteLine({ run }, clock)).toBe(
      'Done: 3 modules, 1,032 passed, 0 failed\nTook 23m 52s, finished at +1432s',
    )
  })
})

describe('when it shows', () => {
  test('a running run; an ended one until code changes after it', () => {
    const run = parseSuite(FILE)!
    expect(isSuiteShown(run, { lastEditAt: T0 + 3600_000 })).toBe(true)
    const ended = { ...run, finishedAt: T0 }
    expect(isSuiteShown(ended, { lastEditAt: 0 })).toBe(true)
    expect(isSuiteShown(ended, { lastEditAt: T0 + 1 })).toBe(false)
  })
})

describe('a run left without an end', () => {
  const base = { now: T0, writtenAt: T0, seenTestingAt: null, isTesting: false, history: {} }

  test('runs while a test runs in ps, however long its file goes unchanged', () => {
    const run = parseSuite(FILE)!
    expect(settle(run, { ...base, now: T0 + 3600_000, isTesting: true }).finishedAt).toBe(null)
  })

  test('is stopped two polls after the band last saw it in ps', () => {
    const run = parseSuite(FILE)!
    const seen = { ...base, seenTestingAt: T0 + 60_000 }
    expect(settle(run, { ...seen, now: T0 + 60_000 + STOPPED_AFTER_MS }).finishedAt).toBe(null)
    const stopped = settle(run, { ...seen, now: T0 + 60_000 + STOPPED_AFTER_MS + 1 })
    expect(stopped.isStopped).toBe(true)
    expect(stopped.finishedAt).toBe(T0 + 60_000)
    expect(stopped.modules.map(m => m.status)).toEqual(['passed', 'stopped', 'pending'])
    // A write after the band last saw it is the later sign.
    expect(settle(run, { ...seen, writtenAt: T0 + 65_000, now: T0 + 70_000 }).finishedAt).toBe(null)
  })

  test('never seen in ps, waits ten minutes, or twice the running module\'s time', () => {
    const run = parseSuite(FILE)!
    expect(settle(run, { ...base, now: T0 + 5 * 60_000 }).finishedAt).toBe(null)
    expect(settle(run, { ...base, now: T0 + 11 * 60_000 }).isStopped).toBe(true)
    expect(settle(run, { ...base, now: T0 + 13 * 60_000, history: { leads_test: [420] } }).finishedAt).toBe(null)
  })

  test('a finished run is left as it is', () => {
    const run = { ...parseSuite(FILE)!, finishedAt: T0 }
    expect(settle(run, { ...base, now: T0 + 3600_000 })).toBe(run)
  })

  test('says how far it got', () => {
    const run = settle(parseSuite(FILE)!, { ...base, seenTestingAt: T0 + 370_000, now: T0 + 400_000 })
    expect(suiteLine({ run }, clock)).toBe(
      'Stopped: 1 of 3 modules, 114 passed, 0 failed\nRan 6m 10s, stopped at +370s',
    )
  })
})
