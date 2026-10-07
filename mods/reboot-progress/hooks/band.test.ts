import { expect, test } from 'claude-code/testing'

const PLUGIN = 'reboot-progress'

// The test runtime has timers; the hooks module's typings don't declare them.
const wait = (ms: number) =>
  new Promise<void>(resolve =>
    (globalThis as unknown as { setTimeout: (f: () => void, ms: number) => void }).setTimeout(resolve, ms),
  )
const BAND = { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 120 }

for (const surface of ['terminal', 'desktop'] as const) {
  test(`the band follows the build on ${surface}`, async ($, on) => {
    // Stand in for the engine beneath: every tool call succeeds.
    on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
    on('fs.exists', () => ({ value: false }) as never)
    // The engine's own band is empty.
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })

    const empty = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect(await empty.findAll({ text: /Progress/ })).toEqual([])
    await empty.unmount()

    await $.tool.call({ tool: 'Skill', skill: 'reboot:build' })
    await $.tool.call({ tool: 'Write', file_path: '/w/app/api/app/v1/app.py', content: '' })
    await $.tool.call({
      tool: 'Write',
      file_path: '/w/app/backend/src/servicers/app.py',
      content: 'def authorizer(self): ...',
    })

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect((await band.findAll({ type: 'Text', text: /Access rules · 5 of 8/ })).length).toBe(1)
    expect((await band.findAll({ type: 'Text', text: /^█+$/ })).length).toBe(1)

    await band.press({ key: 'hide' })
    expect(await band.findAll({ text: /Progress/ })).toEqual([])
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`the activity columns draw on ${surface}`, async ($, on) => {
    on('fs.exists', () => ({ value: false }) as never)
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    // Haiku names the task in both tenses; the prompt goes through.
    on('model.complete', () => ({ value: { isAnswered: true, text: 'Writing the servicers\nWrote the servicers' } }) as never)
    on('prompt.submit', ($, e) => ({ text: e.text }) as never)

    await $.prompt.submit({ text: 'Write the servicers for the app, then the tests.' } as never)
    await wait(50) // the summary runs in the background

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    for (const text of ['Just completed', 'Now', 'Writing the servicers']) {
      expect((await band.findAll({ type: 'Text', text })).length).toBeGreaterThan(0)
    }
  })
}
