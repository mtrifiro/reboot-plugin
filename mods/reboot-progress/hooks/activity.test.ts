import { describe, expect, test } from 'claude-code/testing'

import { WAITING, endTurn, fallback, isWorthSummarizing, parseSummary, startTask, summaryPrompt, textOf } from './activity'

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

  test('reads both tenses from a reply', () => {
    expect(parseSummary('"Writing the Google access servicers."\nWrote the Google access servicers.\n')).toEqual({
      now: 'Writing the Google access servicers',
      done: 'Wrote the Google access servicers',
    })
    expect(parseSummary('1. Writing tests\n2. Wrote tests')).toEqual({ now: 'Writing tests', done: 'Wrote tests' })
    expect(parseSummary('Writing tests')).toEqual({ now: 'Writing tests', done: 'Writing tests' })
    expect(parseSummary('  \n')).toBe(null)
    expect(parseSummary('x'.repeat(100))!.now.length).toBe(60)
  })

  test('falls back to the first sentence', () => {
    expect(fallback('**Now** writing the servicers. Then the tests.')).toBe('Now writing the servicers')
  })

  test('a new task moves the current one to Just completed', () => {
    const api = { now: 'Writing the API', done: 'Wrote the API' }
    const servicers = { now: 'Writing the servicers', done: 'Wrote the servicers' }
    const first = startTask(null, api, { justCompleted: null, now: WAITING })
    expect(first).toEqual({ justCompleted: null, now: 'Writing the API' })
    const second = startTask(api, servicers, first)
    expect(second).toEqual({ justCompleted: 'Wrote the API', now: 'Writing the servicers' })
    // The same task again changes nothing.
    expect(startTask(servicers, { ...servicers }, second)).toEqual(second)
  })

  test('a new turn keeps the last Just completed until a task replaces it', () => {
    const shown = { justCompleted: 'Wrote the API', now: WAITING }
    expect(startTask(null, { now: 'Planning tests', done: 'Planned tests' }, shown)).toEqual({
      justCompleted: 'Wrote the API',
      now: 'Planning tests',
    })
  })

  test('the end of a turn completes the last task and waits', () => {
    expect(endTurn({ now: 'Writing tests', done: 'Wrote tests' }, null)).toEqual({ justCompleted: 'Wrote tests', now: WAITING })
    expect(endTurn(null, { justCompleted: 'Wrote the API', now: 'x' })).toEqual({ justCompleted: 'Wrote the API', now: WAITING })
  })

  test('the prompt carries the text and asks for a short phrase', () => {
    expect(summaryPrompt('Build it.', 'request')).toContain('<text>\nBuild it.\n</text>')
    expect(summaryPrompt('Build it.', 'narration')).toContain('past tense')
  })
})
