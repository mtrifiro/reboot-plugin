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
    expect(await empty.findAll({ text: /Reboot/ })).toEqual([])
    await empty.unmount()

    await $.tool.call({ tool: 'Skill', skill: 'reboot:build' })
    await $.tool.call({ tool: 'Write', file_path: '/w/app/api/app/v1/app.py', content: '' })
    await $.tool.call({
      tool: 'Write',
      file_path: '/w/app/backend/src/servicers/app.py',
      content: 'def authorizer(self): ...',
    })

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    // The kind of work beside the bar, not the stage.
    expect((await band.findAll({ type: 'Text', text: /^Building\s*$/ })).length).toBe(1)
    expect(await band.findAll({ type: 'Text', text: /access rules|backend|screens|·/ })).toEqual([])
    expect((await band.findAll({ type: 'Text', text: /^█+$/ })).length).toBeGreaterThan(0)

    await $.command.run({ command: 'reboot-progress', args: 'hide' } as never)
    expect(await band.findAll({ text: /Reboot/ })).toEqual([])
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`the activity columns draw on ${surface}`, async ($, on) => {
    on('fs.exists', () => ({ value: false }) as never)
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    // The model names the task; the prompt goes through.
    on('model.complete', () => ({ value: { isAnswered: true, text: 'Writing the servicers\nWrote the servicers' } }) as never)
    on('prompt.submit', ($, e) => ({ text: e.text }) as never)

    await $.prompt.submit({ text: 'Write the servicers for the app, then the tests.' } as never)
    await wait(50) // the summary runs in the background

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect((await band.findAll({ type: 'Text', text: 'Writing the servicers' })).length).toBe(1)
    // The status alone, with no Now heading over it.
    expect(await band.findAll({ type: 'Text', text: /^Now$/ })).toEqual([])
    expect(await band.findAll({ type: 'Text', text: /Just completed/ })).toEqual([])
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`a typed /reboot:app shows the bar at once on ${surface}`, async ($, on) => {
    on('fs.exists', () => ({ value: false }) as never)
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    on('model.complete', () => ({ value: { isAnswered: true, text: 'NOW: Planning the dashboard\nDONE: NONE' } }) as never)
    on('prompt.submit', ($, e) => ({ text: e.text }) as never)

    await $.prompt.submit({ text: '/reboot:app build a user friendly interface to Google Analytics' } as never)

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect((await band.findAll({ type: 'Text', text: /Reboot/ })).length).toBe(1)
    // Planning, the current step, already shows a little.
    expect((await band.findAll({ type: 'Text', text: /^█+$/ })).length).toBeGreaterThan(0)
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`a prompt the summary calls a fix starts a bar on ${surface}`, async ($, on) => {
    on('fs.exists', () => ({ value: false }) as never)
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    on('model.complete', () =>
      ({ value: { isAnswered: true, text: 'NOW: Fixing the sign-in button\nDONE: NONE\nTASK: NEW FIX' } }) as never,
    )
    on('prompt.submit', ($, e) => ({ text: e.text }) as never)

    await $.prompt.submit({ text: 'The sign-in button does nothing when I click it.' } as never)
    await wait(50) // the summary runs in the background

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect((await band.findAll({ type: 'Text', text: /^Reboot$/ })).length).toBe(1)
    expect((await band.findAll({ type: 'Text', text: 'Fixing the sign-in button' })).length).toBe(1)
    expect((await band.findAll({ type: 'Text', text: /^Fixing\s*$/ })).length).toBe(1)
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`the Dashboard button opens the dashboard in the browser on ${surface}`, async ($, on) => {
    const opened: string[][] = []
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
    on('session.cwd', () => ({ value: '/w/app' }) as never)
    on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
    on('fs.read', () => ({ value: '' }) as never)
    on('ui.status', () => ({ value: undefined }) as never)
    on('process.run', ($, e) => {
      const argv = (e as { argv: string[] }).argv
      if (argv[0] === 'open') opened.push(argv)
      const stdout = argv[0] === 'lsof' ? 'rbt 1 me 3u IPv4 0t0 TCP 127.0.0.1:9871 (LISTEN)' : ''
      return { value: { exitCode: 0, stdout, stderr: '' } } as never
    })

    // Starting the app checks what is serving, which finds the dashboard.
    await $.tool.call({ tool: 'Bash', command: 'uv run rbt dev run' })
    await wait(50)

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    await band.press({ key: 'dashboard' })
    expect(opened).toEqual([['open', 'http://127.0.0.1:9871/']])
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`Now leaves "Waiting for you" the moment a prompt is sent on ${surface}`, async ($, on) => {
    on('fs.exists', () => ({ value: false }) as never)
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    // The summary never comes back: Now must still not wait.
    on('model.complete', () => ({ value: { isAnswered: false, reason: 'empty-reply' } }) as never)
    on('prompt.submit', ($, e) => ({ text: e.text }) as never)

    await $.prompt.submit({ text: "let's add the YOY feature" } as never)

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect(await band.findAll({ type: 'Text', text: /Waiting for you/ })).toEqual([])
  })
}
