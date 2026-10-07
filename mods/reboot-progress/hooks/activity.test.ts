import { describe, expect, test } from 'claude-code/testing'

import { cleanSummary, fallback, isWorthSummarizing, summaryPrompt, textOf, waiting } from './activity'

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

  test('cleans a model reply to one short line', () => {
    expect(cleanSummary('"Writing the Google access servicers."\n')).toBe('Writing the Google access servicers')
    expect(cleanSummary('x'.repeat(100)).length).toBe(70)
  })

  test('falls back to the first sentence', () => {
    expect(fallback('**Now** writing the servicers. Then the tests.')).toBe('Now writing the servicers')
  })

  test('says when it waits', () => {
    expect(waiting(null)).toBe('Waiting for you')
    expect(waiting('Writing the servicers')).toBe('Waiting for you · Writing the servicers')
  })

  test('the prompt carries the text and asks for a short phrase', () => {
    expect(summaryPrompt('Build it.', 'request')).toContain('<text>\nBuild it.\n</text>')
    expect(summaryPrompt('Build it.', 'narration')).toContain('3 to 8 words')
  })
})
