// Pure logic: the text a summary is made from, the prompt that asks for
// it, the fallback when no summary comes back, and how the band's
// "Just completed" and "Now" move as tasks change.

import type { Activity } from '../types'
import type { Decision } from './progress'

/**
 * What one text says, as the model reads it: what is being done now (null
 * when the text only explains or plans, so Now stays), what it says was
 * just finished (null when it says nothing is), and for a request whether
 * it starts new work (null when the reply doesn't say).
 */
export type Summary = { now: string | null; done: string | null; decision: Decision | null }

export const WAITING = 'Idle'

/** Now, from the moment a prompt is sent until its summary names the work. */
export const STARTING = 'Working on your request'

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

/**
 * The prompt for one summary. A request also asks whether it starts new
 * work, judged against `current`, the work under way in a few words, and
 * `lastReply`, the assistant's message it answers: a bare "2" or "do it"
 * means nothing without the list or proposal before it.
 */
export const summaryPrompt = (
  text: string,
  kind: 'narration' | 'request',
  current = 'none',
  lastReply = '',
): string =>
  (kind === 'narration'
    ? 'Below is what a coding assistant just told the user while building their app.'
    : 'Below is what a user just asked a coding assistant to do.') +
  ' Reply with exactly ' +
  (kind === 'request' ? 'three' : 'two') +
  ' lines and nothing else:\n' +
  (kind === 'request'
    ? 'NOW: one sentence, 10 to 25 words, starting with a verb ending in -ing, on what the ' +
      'assistant now starts on for this request (for a question, what it is looking ' +
      'into). Never NONE.\n'
    : 'NOW: one sentence, 10 to 25 words, starting with a verb ending in -ing, on the work ' +
      'happening at this moment; or NONE if the text only explains, reports or plans.\n') +
  'DONE: work on the app the text says was just finished, in 3 to 8 words in the past ' +
  'tense; or NONE. A proposal, design or result the text hands the user to review counts ' +
  'as finished ("Drafted the design for your review"). Never planned, upcoming or ' +
  'ongoing work.\n' +
  (kind === 'request'
    ? 'TASK: whether this request starts new work: NEW BUILD (a whole new app), NEW ' +
      'FEATURE (a new capability, or a change to one, in an existing app), NEW FIX (fixing ' +
      'something that is broken), or SAME (a follow-up, an answer, an approval or a small ' +
      `tweak within the current work). The current work: ${current}. A request that ` +
      'picks or approves new work the assistant proposed ("2", "do it", "yes, build ' +
      'that") starts that work; asking for ideas, suggestions or options does not.\n'
    : '') +
  '\n' +
  'NOW is for the developer watching the build: name the concrete things the work ' +
  'touches, by their real names from the text: state types, their methods and fields, ' +
  'modules and files, screens, scenarios. Say what is happening to them (adding, ' +
  'changing, wiring, testing) and why when the text says. Describe the work, never the ' +
  'talking ("Describing", "Explaining", "Outlining"). Plain names, no backticks or ' +
  'markdown.\n' +
  'Good NOW: "Adding a compare_years reader to the Site state type and a Last year toggle ' +
  'to Dashboard.tsx, so each number can show the same period a year earlier".\n' +
  'Good NOW: "Running the what_changed scenarios after fixing the off-by-one in ' +
  'sample.py that seeded 89 days instead of 90".\n' +
  'DONE stays short and plain ("Finished the data model").\n' +
  'No quotes, no trailing periods.\n\n' +
  (kind === 'request' && lastReply
    ? `<assistant_last_message>\n${lastReply.slice(0, 2000)}\n</assistant_last_message>\n\n`
    : '') +
  '<text>\n' +
  text.slice(0, 4000) +
  '\n</text>'

/** One line's cleanup: no quotes, backticks, list marks or trailing period, at most `max` characters. */
const cleanLine = (line: string, max = 60) =>
  clip(line.trim().replace(/^[-*\d.)\s]+/, '').replace(/`/g, '').replace(/^["']+|["'.]+$/g, ''), max)

/** How long Now may run: one descriptive sentence, wrapping onto a second line. */
export const NOW_MAX = 200

/** A TASK line's answer. */
function decisionOf(raw: string | undefined): Decision | null {
  const t = (raw ?? '').toUpperCase()
  if (/\bSAME\b/.test(t)) return 'same'
  if (/\bBUILD\b/.test(t)) return 'build'
  if (/\bFEATURE\b/.test(t)) return 'feature'
  if (/\bFIX\b/.test(t)) return 'fix'
  return null
}

/**
 * The summary in a `NOW:` / `DONE:` (/ `TASK:`) reply. The model sometimes
 * drops the labels: then the first line is Now and the second Done. null
 * when there is no Now.
 */
export function parseSummary(reply: string): Summary | null {
  const lines = reply.split('\n').map(l => l.trim()).filter(l => l.length > 0)
  const labeled = (label: string) =>
    lines.find(l => l.toUpperCase().startsWith(`${label}:`))?.slice(label.length + 1)
  const nowText = labeled('NOW') ?? (lines.some(l => /^(DONE|TASK):/i.test(l)) ? undefined : lines[0])
  if (nowText === undefined) return null
  const doneText = labeled('DONE') ?? (labeled('NOW') === undefined ? lines[1] : undefined)
  const phrase = (raw: string | undefined, max?: number) => {
    const line = raw === undefined ? '' : cleanLine(raw, max)
    return line === '' || /^none$/i.test(line) ? null : line
  }

  return {
    now: phrase(nowText, NOW_MAX),
    done: phrase(doneText),
    decision: decisionOf(labeled('TASK')),
  }
}

/** The first sentence of `text`, clipped: what shows when no summary comes back. */
export function fallback(text: string): string {
  const plain = text.replace(/[*_`#>]/g, '').replace(/\s+/g, ' ').trim()
  const sentence = plain.match(/^.+?[.!?](?=\s|$)/)?.[0] ?? plain

  return clip(sentence.replace(/[.!?]$/, ''), NOW_MAX)
}

const clip = (s: string, max: number) => (s.length <= max ? s : `${s.slice(0, max - 1).trimEnd()}…`)

/**
 * A new text while working: Now follows it, and Just completed changes
 * only when the text says something was finished.
 */
export const startTask = (task: Summary, shown: Activity | null): Activity => ({
  justCompleted: task.done ?? shown?.justCompleted ?? null,
  now: task.now ?? shown?.now ?? WAITING,
})

/** The turn is over: Just completed stays, and Now waits. */
export const endTurn = (shown: Activity | null): Activity => ({
  justCompleted: shown?.justCompleted ?? null,
  now: WAITING,
})
