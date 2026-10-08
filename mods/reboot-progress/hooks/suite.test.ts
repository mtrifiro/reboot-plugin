import { describe, expect, test } from 'claude-code/testing'

import { expectedFinish, isSuiteShown, parseSuite, remember, suiteLine, typical } from './suite'

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
  })
})

describe('the expected finish', () => {
  test('is the median of the last runs, each module at most five', () => {
    let h = {}
    for (const s of [100, 300, 200, 900, 250, 260]) {
      h = remember(h, { startedAt: 0, finishedAt: 1, modules: [{ name: 'a', status: 'passed', passed: 1, failed: 0, seconds: s, startedAt: null }] })
    }
    expect((h as Record<string, number[]>).a).toEqual([300, 200, 900, 250, 260])
    expect(typical(h, 'a')).toBe(260)
    expect(typical(h, 'none')).toBe(null)
  })

  test("is the running module's time left plus each pending module's", () => {
    const run = parseSuite(FILE)!
    const h = { leads_test: [100], web_test: [420] }
    // leads_test started when accounts_test ended (130.1 s in); 30 s later
    // it has 70 s left, then web_test's 420.
    expect(expectedFinish(run, h, T0 + 160_100)).toBe(T0 + 160_100 + 490_000)
    // Past its typical time, the running module adds nothing.
    expect(expectedFinish(run, h, T0 + 400_000)).toBe(T0 + 400_000 + 420_000)
  })

  test('is not given without history for every module still to run', () => {
    expect(expectedFinish(parseSuite(FILE)!, { leads_test: [100] }, T0)).toBe(null)
  })
})

describe('the line', () => {
  test('while it goes: modules done, failures, and the finish with history', () => {
    const run = parseSuite(FILE)!
    expect(suiteLine({ run, expectedAt: T0 + 650_000 }, clock)).toBe('Tests · 1 of 3 modules · 0 failed · done ≈ +650s')
    expect(suiteLine({ run, expectedAt: null }, clock)).toBe('Tests · 1 of 3 modules · 0 failed')
  })

  test('names a failure at once, and a rerun apart from failures', () => {
    const run = parseSuite(FILE)!
    run.modules[0]!.status = 'failed'
    run.modules[1]!.status = 'rerun'
    expect(suiteLine({ run, expectedAt: null }, clock)).toBe('Tests · 2 of 3 modules · 1 failed: accounts_test · 1 rerun')
  })

  test('once it ends: the result and the time it took', () => {
    const run = parseSuite(FILE)!
    run.finishedAt = T0 + 1432_000
    run.modules.forEach(m => (m.status = 'passed'))
    expect(suiteLine({ run, expectedAt: null }, clock)).toBe('Tests passed · 3 modules · 23m 52s')
    run.modules[2]!.status = 'failed'
    expect(suiteLine({ run, expectedAt: null }, clock)).toBe('Tests failed · 1 failed: web_test · 3 modules · 23m 52s')
  })
})

describe('when it shows', () => {
  const base = { now: T0, writtenAt: T0, lastEditAt: 0, isTesting: false, history: {} }

  test('a finished run, until code changes after it', () => {
    const run = { ...parseSuite(FILE)!, finishedAt: T0 }
    expect(isSuiteShown(run, base)).toBe(true)
    expect(isSuiteShown(run, { ...base, lastEditAt: T0 + 1 })).toBe(false)
  })

  test('a running one, unless abandoned: no tests in ps and its file long unchanged', () => {
    const run = parseSuite(FILE)!
    expect(isSuiteShown(run, { ...base, now: T0 + 3600_000, isTesting: true })).toBe(true)
    expect(isSuiteShown(run, { ...base, now: T0 + 5 * 60_000 })).toBe(true)
    expect(isSuiteShown(run, { ...base, now: T0 + 11 * 60_000 })).toBe(false)
    // A module that typically takes 7 minutes may go 14 without a write.
    expect(isSuiteShown(run, { ...base, now: T0 + 13 * 60_000, history: { leads_test: [420] } })).toBe(true)
  })
})
