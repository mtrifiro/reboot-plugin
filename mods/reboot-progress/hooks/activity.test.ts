import { describe, expect, test } from 'claude-code/testing'

import { WAITING, endTurn, isTesting, testCommand, testLine, testProgress, fallback, isWorthSummarizing, parseSummary, startTask, summaryPrompt, textOf } from './activity'

describe('activity', () => {
  test('reads the text blocks of a row', () => {
    expect(textOf('  plain  ')).toBe('plain')
    expect(
      textOf([
        { type: 'text', text: 'Now writing the servicers.' },
        { type: 'tool_use', id: 'x' },
        { type: 'text', text: 'Then tests.' },
      ]),
    ).toBe('Now writing the servicers.\nThen tests.')
    expect(textOf(undefined)).toBe('')
  })

  test('skips short asides', () => {
    expect(isWorthSummarizing('Done.')).toBe(false)
    expect(isWorthSummarizing('Now writing the servicers: Google access and the demo data.')).toBe(true)
  })

  test('reads Now and Done from a labeled reply', () => {
    expect(parseSummary('NOW: Writing the React dashboard.\nDONE: Finished the backend.')).toEqual({
      now: 'Writing the React dashboard',
      done: 'Finished the backend',
      decision: null,
    })
    // A request's third line says whether it starts new work.
    expect(parseSummary('NOW: Fixing the login error\nDONE: NONE\nTASK: NEW FIX')!.decision).toBe('fix')
    expect(parseSummary('NOW: Making the button blue\nDONE: NONE\nTASK: SAME')!.decision).toBe('same')
    expect(parseSummary('NOW: Adding transfers\nDONE: NONE\nTASK: NEW FEATURE')!.decision).toBe('feature')
    expect(parseSummary('now: "Choosing chart colors"\ndone: NONE')).toEqual({ now: 'Choosing chart colors', done: null, decision: null })
    // Unlabeled, as the model sometimes replies: the first line is Now, the second Done.
    expect(parseSummary('Designing the chart series\nNONE')).toEqual({ now: 'Designing the chart series', done: null, decision: null })
    expect(parseSummary('Writing tests\nFinished the servicers')).toEqual({ now: 'Writing tests', done: 'Finished the servicers', decision: null })
    expect(parseSummary('Writing tests')).toEqual({ now: 'Writing tests', done: null, decision: null })
    expect(parseSummary('DONE: Finished the backend')).toBe(null)
    expect(parseSummary('  \n')).toBe(null)
    // NOW: NONE when the text only explains or plans: Now stays as it was.
    expect(parseSummary('NOW: NONE\nDONE: NONE')).toEqual({ now: null, done: null, decision: null })
    expect(parseSummary(`NOW: ${'x'.repeat(300)}`)!.now!.length).toBe(200)
    expect(parseSummary('NOW: Adding `compare_years` to Site')!.now).toBe('Adding compare_years to Site')
  })

  test('falls back to the first sentence', () => {
    expect(fallback('**Now** writing the servicers. Then the tests.')).toBe('Now writing the servicers')
  })

  test('Just completed changes only when a text says something finished', () => {
    const start = { justCompleted: null, now: WAITING }
    const writing = startTask({ now: 'Writing the React dashboard', done: 'Finished the backend', decision: null }, start)
    expect(writing).toEqual({ justCompleted: 'Finished the backend', now: 'Writing the React dashboard' })
    // A sub-step is not a finish: Just completed stays.
    expect(startTask({ now: 'Choosing chart colors', done: null, decision: null }, writing)).toEqual({
      justCompleted: 'Finished the backend',
      now: 'Choosing chart colors',
    })
  })

  test('a text that only explains keeps Now', () => {
    const shown = { justCompleted: null, now: 'Writing the code that builds the report' }
    expect(startTask({ now: null, done: null, decision: null }, shown)).toEqual(shown)
  })

  test('the end of a turn waits and keeps Just completed', () => {
    expect(endTurn({ justCompleted: 'Finished the backend', now: 'x' })).toEqual({
      justCompleted: 'Finished the backend',
      now: WAITING,
    })
    expect(endTurn(null)).toEqual({ justCompleted: null, now: WAITING })
  })

  test('the prompt carries the text and asks for a short phrase', () => {
    expect(summaryPrompt('Build it.', 'request')).toContain('<text>\nBuild it.\n</text>')
    // A request carries the message it answers; a narration does not.
    expect(summaryPrompt('2', 'request', 'none', '1. Weekly email\n2. What changed')).toContain(
      '<assistant_last_message>\n1. Weekly email\n2. What changed\n</assistant_last_message>',
    )
    expect(summaryPrompt('Writing.', 'narration', 'none', 'x')).not.toContain('assistant_last_message')
    expect(summaryPrompt('Build it.', 'narration')).toContain('by their real names')
  })
})

describe('a test run between turns', () => {
  test('pytest, vitest, Playwright and npm test count; servers and searches do not', () => {
    expect(isTesting('/w/app/.venv/bin/python /w/app/.venv/bin/pytest tests -m critical')).toBe(true)
    expect(isTesting('node /w/app/web/node_modules/.bin/vitest run')).toBe(true)
    expect(isTesting('node /n/.bin/playwright test --project=chromium')).toBe(true)
    expect(isTesting('npm run test')).toBe(true)
    expect(isTesting('rbt dev run\nnpm run dev\nrbt dashboard')).toBe(false)
    expect(isTesting('grep -r pytest .')).toBe(false)
  })
})

describe('test progress', () => {
  test("reads pytest's percentages and failures, dots or verbose", () => {
    const dots = 'collected 40 items\n\ntests/test_a.py ..F.....  [ 20%]\ntests/test_b.py ....E...  [ 40%]\n'
    expect(testProgress(dots)).toEqual({ percent: 40, failed: 2 })
    const verbose =
      'tests/test_a.py::test_one PASSED                     [ 50%]\ntests/test_a.py::test_two FAILED                     [100%]\n'
    expect(testProgress(verbose)).toEqual({ percent: 100, failed: 1 })
  })

  test("reads Playwright's counts, and says nothing of output that doesn't say", () => {
    expect(testProgress('  [3/12] [chromium] › a.spec.ts:4:1 › signs in\n  ✘  1 [chromium] › b.spec.ts\n')).toEqual({
      percent: 25,
      failed: 1,
    })
    expect(testProgress('')).toEqual({ percent: null, failed: 0 })
  })

  test('the line names how far the run is and its time so far', () => {
    const run = { command: 'pytest tests', startedAt: 0, seenAt: 0, outputPath: null, percent: 42, failed: 2 }
    expect(testLine(run, 72_000)).toBe('Waiting for the tests to finish: 42% done, 2 failed · 1m 12s')
    expect(testLine({ ...run, percent: null, failed: 0 }, 9_000)).toBe('Waiting for the tests to finish · 9s')
  })

  test('the command, from the runner to a pipe', () => {
    const ps = '  9 /w/.venv/bin/python /w/.venv/bin/pytest tests/web_test.py -q -k signs\n 10 grep pytest'
    expect(testCommand(ps)).toBe('pytest tests/web_test.py -q -k signs')
    expect(testCommand('timeout 900 uv run pytest tests -q 2>&1 | tail -3')).toBe('pytest tests -q')
    expect(testCommand('rbt dev run')).toBe(null)
    // The shell Claude Code starts, and the runner it runs: one command.
    const shell = "  8 /bin/zsh -c eval 'uv run pytest tests -k \"signs in\"' < /dev/null && pwd -P"
    expect(testCommand(shell)).toBe(testCommand('  9 /w/.venv/bin/python /w/.venv/bin/pytest tests -k signs in'))
  })
})

describe("a project's own test run", () => {
  test('a runner is a word of its own, and the run names a path in the project', () => {
    expect(testCommand('  9 vim pytest.ini')).toBe(null)
    expect(testCommand('  9 /w/app/.venv/bin/python /w/app/.venv/bin/pytest -q', '/w/app')).toBe('pytest -q')
    expect(testCommand('  9 /w/other/.venv/bin/pytest -q', '/w/app')).toBe(null)
    expect(isTesting('  9 /w/other/.venv/bin/pytest -q', '/w/app')).toBe(false)
  })
})
