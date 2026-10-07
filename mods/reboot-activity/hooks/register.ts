import type { EngineInterface, Register } from 'claude-code'

import { cleanSummary, fallback, isWorthSummarizing, summaryPrompt, textOf, waiting } from './activity'

// The module's own; a reload starts them over.
let last: string | null = null
let isTurnActive = false
let latest = 0 // the newest summary asked for; older replies are dropped

/** Shows what is being worked on: `text`, or Waiting once the turn is over. */
function show($: EngineInterface, text: string) {
  last = text
  $.ui.status(isTurnActive ? text : waiting(text))
}

/** Summarizes `text` with a small model in the background, newest wins. */
async function summarize($: EngineInterface, text: string, kind: 'narration' | 'request') {
  const id = ++latest
  let summary = ''
  try {
    const reply = await $.model.complete({
      model: 'haiku',
      prompt: summaryPrompt(text, kind),
      maxTokens: 40,
      timeoutMs: 15000,
    })
    if (reply.isAnswered) summary = cleanSummary(reply.text)
  } catch {
    summary = ''
  }
  if (id !== latest) return
  show($, summary || fallback(text))
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    $.ui.status(waiting(null))

    return next(e)
  })

  on('prompt.submit', async ($, e, next) => {
    isTurnActive = true
    if (e.text.trim()) void summarize($, e.text, 'request')

    return next(e)
  }).catch(($, e, next) => next(e))

  // The model's own narration on the main thread, not a subagent's.
  on('session.append', { door: 'response' }, async ($, e, next) => {
    const appended = await next(e)
    if (e.agentId === undefined && e.message.type === 'assistant') {
      const text = textOf(e.message.content)
      if (isWorthSummarizing(text)) void summarize($, text, 'narration')
    }

    return appended
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    isTurnActive = false
    $.ui.status(waiting(last))

    return next(e)
  })
}
