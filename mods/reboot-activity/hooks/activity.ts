// Pure logic: the text a summary is made from, the prompt that asks for
// it, and the fallback when no summary comes back.

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
  ' In 3 to 8 words, say what the assistant is working on now, as a present-tense ' +
  'phrase starting with a verb ending in -ing ("Writing the Google access servicers"). ' +
  'No quotes, no trailing period, nothing else.\n\n<text>\n' +
  text.slice(0, 4000) +
  '\n</text>'

/** A summary's cleanup: one line, no quotes or trailing period, at most 70 characters. */
export function cleanSummary(reply: string): string {
  const line = reply.split('\n').map(l => l.trim()).find(l => l.length > 0) ?? ''

  return clip(line.replace(/^["'`]+|["'`.]+$/g, ''), 70)
}

/** The first sentence of `text`, clipped: what shows when no summary comes back. */
export function fallback(text: string): string {
  const plain = text.replace(/[*_`#>]/g, '').replace(/\s+/g, ' ').trim()
  const sentence = plain.match(/^.+?[.!?](?=\s|$)/)?.[0] ?? plain

  return clip(sentence.replace(/[.!?]$/, ''), 70)
}

const clip = (s: string, max: number) => (s.length <= max ? s : `${s.slice(0, max - 1).trimEnd()}…`)

export const waiting = (last: string | null): string =>
  last ? `Waiting for you · ${last}` : 'Waiting for you'
