import { describe, expect, test } from 'claude-code/testing'

import { summaryPrompt } from './activity'
import { voiced } from './voice'

describe('Sassy mode', () => {
  test("rewords the band's own lines and toasts, keeping their facts", () => {
    expect(voiced('Idle', true)).toBe('Idle. Blissfully.')
    expect(voiced('Reboot app stopped', true)).toBe('The app stopped. Rude.')
    expect(voiced('Deploy failed: no permission', true)).toBe('Deploy failed: no permission. Not my finest hour.')
    expect(voiced('Waiting for the tests to finish · 1m 12s of about 6m', true)).toBe(
      'Waiting on the tests, no pressure · 1m 12s of about 6m',
    )
    expect(voiced('So far: 3 of 9 modules, 40 passed, 0 failed\nLeft: 6 modules', true)).toBe(
      'So far, so good: 3 of 9 modules, 40 passed, 0 failed\nLeft: 6 modules',
    )
    expect(voiced('Done: 9 modules, 90 passed, 2 failed (web_test)\nTook 9m 00s', true)).toBe(
      'Done, awkwardly: 9 modules, 90 passed, 2 failed (web_test)\nTook 9m 00s',
    )
  })

  test('leaves alone what it has no wording for, and everything when off', () => {
    expect(voiced('Adding a transfer method to Account', true)).toBe('Adding a transfer method to Account')
    expect(voiced('Idle', false)).toBe('Idle')
  })

  test("asks the summaries for the voice, and only when it's on", () => {
    expect(summaryPrompt('Build it.', 'narration', 'none', '', true)).toContain('Voice: sassy')
    expect(summaryPrompt('Build it.', 'narration')).not.toContain('Voice: sassy')
  })
})
