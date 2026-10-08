// Pure logic: Sassy mode's voice for the band's own words, its fixed
// lines and its toasts. The summaries the model writes take the voice from
// their prompt (`summaryPrompt`); the facts in a line (names, counts,
// times, reasons) are kept as they are.

/** Each plain wording and its sassy one; the first that matches wins. */
const SASS: [RegExp, string][] = [
  [/^Idle$/, 'Idle. Blissfully.'],
  [/^Working on your request$/, 'On it. Obviously.'],
  [/^Waiting for the tests to finish/, 'Waiting on the tests, no pressure'],
  [/^So far: (.*\b0 failed\b)/, 'So far, so good: $1'],
  [/^So far: /, 'So far, so-so: '],
  [/^Done: (.*\b0 failed\b)/, 'Done, and flawless: $1'],
  [/^Done: /, 'Done, awkwardly: '],
  [/^Reboot (app|dashboard) started$/, "The $1 is up. You're welcome."],
  [/^Reboot (app|dashboard) stopped$/, 'The $1 stopped. Rude.'],
  [/^Deployed revision (\d+) to Reboot Cloud$/, 'Revision $1 is on Reboot Cloud. Hold the applause.'],
  [/^Deploy failed: (.*)$/, 'Deploy failed: $1. Not my finest hour.'],
  [/^Deploying to Reboot Cloud: /, 'Shipping it to Reboot Cloud: '],
  [/^Frontend published$/, 'The frontend is out there. Try to act surprised.'],
  [/^Reboot Cloud app is live$/, 'Your app is live on Reboot Cloud. Go on, look.'],
  [/^Copied the (.*)$/, 'Copied the $1. Paste responsibly.'],
]

/** `text` in Sassy mode's voice when it is on; as it is otherwise, or when it has no sassy wording. */
export function voiced(text: string, isSassy: boolean): string {
  if (!isSassy) return text
  const found = SASS.find(([plain]) => plain.test(text))

  return found ? text.replace(found[0], found[1]) : text
}
