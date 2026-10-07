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

  test('reads Now and Done from a labeled reply', () => {
    expect(parseSummary('NOW: Writing the React dashboard.\nDONE: Finished the backend.')).toEqual({
      now: 'Writing the React dashboard',
      done: 'Finished the backend',
    })
    expect(parseSummary('now: "Choosing chart colors"\ndone: NONE')).toEqual({ now: 'Choosing chart colors', done: null })
    // Unlabeled, as Haiku sometimes replies: the first line is Now, the second Done.
    expect(parseSummary('Designing the chart series\nNONE')).toEqual({ now: 'Designing the chart series', done: null })
    expect(parseSummary('Writing tests\nFinished the servicers')).toEqual({ now: 'Writing tests', done: 'Finished the servicers' })
    expect(parseSummary('Writing tests')).toEqual({ now: 'Writing tests', done: null })
    expect(parseSummary('DONE: Finished the backend')).toBe(null)
    expect(parseSummary('  \n')).toBe(null)
    expect(parseSummary(`NOW: ${'x'.repeat(100)}`)!.now.length).toBe(60)
  })

  test('falls back to the first sentence', () => {
    expect(fallback('**Now** writing the servicers. Then the tests.')).toBe('Now writing the servicers')
  })

  test('Just completed changes only when a text says something finished', () => {
    const start = { justCompleted: null, now: WAITING }
    const writing = startTask({ now: 'Writing the React dashboard', done: 'Finished the backend' }, start)
    expect(writing).toEqual({ justCompleted: 'Finished the backend', now: 'Writing the React dashboard' })
    // A sub-step is not a finish: Just completed stays.
    expect(startTask({ now: 'Choosing chart colors', done: null }, writing)).toEqual({
      justCompleted: 'Finished the backend',
      now: 'Choosing chart colors',
    })
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
    expect(summaryPrompt('Build it.', 'narration')).toContain('Plans, next steps')
  })
})
