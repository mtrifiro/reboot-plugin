// Pure logic: the text a summary is made from, the prompt that asks for
// it, the fallback when no summary comes back, and how the band's
// "Just completed" and "Now" move as tasks change.

import type { Activity } from '../types'

/** One task, as Haiku names it: present tense for Now, past for Just completed. */
export type Task = { now: string; done: string }

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
    ? 'Below is what a coding assistant just told the user it is doing.'
    : 'Below is what a user just asked a coding assistant to do.') +
  ' In 3 to 8 words, say what the assistant is working on now. Reply with exactly two ' +
  'lines: first as a present-tense phrase starting with a verb ending in -ing ' +
  '("Writing the Google access servicers"), then the same phrase in the past tense ' +
  '("Wrote the Google access servicers"). No quotes, no trailing periods, nothing else.' +
  '\n\n<text>\n' +
  text.slice(0, 4000) +
  '\n</text>'

/** One phrase's cleanup: no quotes, list marks or trailing period, at most 60 characters. */
const cleanLine = (line: string) =>
  clip(line.trim().replace(/^[-*\d.)\s]+/, '').replace(/^["'`]+|["'`.]+$/g, ''), 60)

/** The task in a reply's two lines; one line serves as both. null when empty. */
export function parseSummary(reply: string): Task | null {
  const lines = reply.split('\n').map(cleanLine).filter(l => l.length > 0)
  if (lines.length === 0) return null

  return { now: lines[0]!, done: lines[1] ?? lines[0]! }
}

/** The first sentence of `text`, clipped: what shows when no summary comes back. */
export function fallback(text: string): string {
  const plain = text.replace(/[*_`#>]/g, '').replace(/\s+/g, ' ').trim()
  const sentence = plain.match(/^.+?[.!?](?=\s|$)/)?.[0] ?? plain

  return clip(sentence.replace(/[.!?]$/, ''), 60)
}

const clip = (s: string, max: number) => (s.length <= max ? s : `${s.slice(0, max - 1).trimEnd()}…`)

/**
 * A new task while working: the one it replaces moves to Just completed.
 * The same task again changes nothing.
 */
export function startTask(current: Task | null, task: Task, shown: Activity | null): Activity {
  if (current !== null && current.now === task.now) return shown ?? { justCompleted: null, now: task.now }
  const justCompleted = current !== null ? current.done : (shown?.justCompleted ?? null)

  return { justCompleted, now: task.now }
}

/** The turn is over: the last task is Just completed, and Now waits. */
export const endTurn = (current: Task | null, shown: Activity | null): Activity => ({
  justCompleted: current?.done ?? shown?.justCompleted ?? null,
  now: WAITING,
})
