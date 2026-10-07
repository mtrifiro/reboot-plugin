// Pure logic: the text a summary is made from, the prompt that asks for
// it, the fallback when no summary comes back, and how the band's
// "Just completed" and "Now" move as tasks change.

import type { Activity } from '../types'

/**
 * What one text says, as the model reads it: what is being done now (null
 * when the text only explains or plans, so Now stays), and what it says
 * was just finished (null when it says nothing is).
 */
export type Task = { now: string | null; done: string | null }

export const WAITING = 'Waiting for you'

/** The text blocks of a row's content, joined; '' when there are none. */
export function textOf(content: unknown): string {
  if (typeof content === 'string') return content.trim()
  if (!Array.isArray(content)) return ''

  return content
    .filter(
      (b): b is { type: 'text'; text: string } =>
        typeof b === 'object' && b !== null && b.type === 'text' && typeof b.text === 'string',
    )
    .map(b => b.text)
    .join('\n')
    .trim()
}

/** Short asides ("Done.", "Let me check.") aren't worth a summary. */
export const isWorthSummarizing = (text: string): boolean => text.length >= 40

export const summaryPrompt = (text: string, kind: 'narration' | 'request'): string =>
  (kind === 'narration'
    ? 'Below is what a coding assistant just told the user while building their app.'
    : 'Below is what a user just asked a coding assistant to do.') +
  ' The user is not a programmer. Reply with exactly two lines and nothing else:\n' +
  'NOW: the work on the app happening at this moment, in 3 to 8 words, as a present-tense ' +
  'phrase starting with a verb ending in -ing; or NONE if the text only explains, reports ' +
  'or plans.\n' +
  'DONE: work on the app the text says was just finished, in 3 to 8 words in the past ' +
  'tense; or NONE. Never planned, upcoming or ongoing work.\n\n' +
  'Both in everyday words the user would understand: say what the work does for the app ' +
  'or its users, not how the code is organized. Never reuse the text\'s technical terms ' +
  '(module, servicer, workflow, schema, pure, I/O, function or file names). Describe the ' +
  'work, never the talking ("Describing", "Explaining", "Outlining").\n' +
  'Bad: "Writing the pure report-shaping module". Good: "Writing the code that builds the ' +
  'report".\n' +
  'Good: "Building the dashboard page", "Fixing a failing test", "Adding sign-in with ' +
  'Google", "Finished the data model".\n' +
  'No quotes, no trailing periods.\n\n<text>\n' +
  text.slice(0, 4000) +
  '\n</text>'

/** One phrase's cleanup: no quotes, list marks or trailing period, at most 60 characters. */
const cleanLine = (line: string) =>
  clip(line.trim().replace(/^[-*\d.)\s]+/, '').replace(/^["'`]+|["'`.]+$/g, ''), 60)

/**
 * The task in a `NOW:` / `DONE:` reply. The model sometimes drops the labels:
 * then the first line is Now and the second Done. null when there is no Now.
 */
export function parseSummary(reply: string): Task | null {
  const lines = reply.split('\n').map(l => l.trim()).filter(l => l.length > 0)
  const labeled = (label: string) =>
    lines.find(l => l.toUpperCase().startsWith(`${label}:`))?.slice(label.length + 1)
  const nowText = labeled('NOW') ?? (lines.some(l => /^DONE:/i.test(l)) ? undefined : lines[0])
  if (nowText === undefined) return null
  const doneText = labeled('DONE') ?? (labeled('NOW') === undefined ? lines[1] : undefined)
  const phrase = (raw: string | undefined) => {
    const line = raw === undefined ? '' : cleanLine(raw)
    return line === '' || /^none$/i.test(line) ? null : line
  }

  return { now: phrase(nowText), done: phrase(doneText) }
}

/** The first sentence of `text`, clipped: what shows when no summary comes back. */
export function fallback(text: string): string {
  const plain = text.replace(/[*_`#>]/g, '').replace(/\s+/g, ' ').trim()
  const sentence = plain.match(/^.+?[.!?](?=\s|$)/)?.[0] ?? plain

  return clip(sentence.replace(/[.!?]$/, ''), 60)
}

const clip = (s: string, max: number) => (s.length <= max ? s : `${s.slice(0, max - 1).trimEnd()}…`)

/**
 * A new text while working: Now follows it, and Just completed changes
 * only when the text says something was finished.
 */
export const startTask = (task: Task, shown: Activity | null): Activity => ({
  justCompleted: task.done ?? shown?.justCompleted ?? null,
  now: task.now ?? shown?.now ?? WAITING,
})

/** The turn is over: Just completed stays, and Now waits. */
export const endTurn = (shown: Activity | null): Activity => ({
  justCompleted: shown?.justCompleted ?? null,
  now: WAITING,
})
